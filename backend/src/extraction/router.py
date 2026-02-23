import asyncio
import os
import structlog
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Annotated, List, Optional
from .service import extract_from_pdf, upload_pdf, detect_quarters
from .schemas import InsurancePlan
from src.database import AsyncSessionLocal
from src.plans.repository import save_plans

router = APIRouter()
logger = structlog.get_logger(__name__)

API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    expected_api_key = os.getenv("API_KEY", "test-secret-key")
    if api_key_header == expected_api_key:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )


VALID_QUARTERS = {"Q1", "Q2", "Q3", "Q4"}


async def _process_single_file(filename: str, content: bytes, quarter_override: Optional[str] = None) -> dict:
    """
    Process a single PDF file: upload, detect quarters, extract plans
    per quarter in parallel, then save to DB sequentially.
    If quarter_override is provided, skip quarter detection entirely.
    """
    log = logger.bind(filename=filename)
    log.info("Processing file", file_size_bytes=len(content), quarter_override=quarter_override)

    file_result = {
        "file": filename,
        "quarters": {},
        "total_plans": 0,
        "inserted": 0,
        "updated_exact": 0,
        "updated_fuzzy": 0,
    }

    # 1. Upload PDF once
    try:
        file_id = await upload_pdf(content)
    except Exception as e:
        log.error("Upload step failed", error=str(e))
        file_result["status"] = "error"
        file_result["detail"] = f"Upload failed: {str(e)}"
        return file_result

    log = log.bind(file_id=file_id)

    # 2. Determine which quarters to extract
    if quarter_override:
        detected = [quarter_override.strip().upper()]
        file_result["detected_quarters"] = detected
        log.info("Using quarter override, skipping detection", quarters=detected)
    else:
        try:
            detected = await detect_quarters(file_id)
            file_result["detected_quarters"] = detected
            log.info("Quarters detected, starting extraction", quarters=detected)
        except Exception as e:
            log.error("Quarter detection step failed", error=str(e))
            file_result["status"] = "error"
            file_result["detail"] = f"Quarter detection failed: {str(e)}"
            return file_result

    # 3. Extract all quarters in parallel (AI calls are the bottleneck)
    async def _extract_quarter(quarter: str):
        try:
            plan_dicts = await extract_from_pdf(file_id, quarter)
            return quarter, plan_dicts, None
        except Exception as e:
            log.error("Extraction failed for quarter", quarter=quarter, error=str(e))
            return quarter, None, str(e)

    extraction_results = await asyncio.gather(
        *[_extract_quarter(q) for q in detected]
    )

    # 4. Save to DB sequentially (own session per file to avoid conflicts)
    log.info("Saving extracted plans to database")
    async with AsyncSessionLocal() as db:
        for quarter, plan_dicts, error in extraction_results:
            if error:
                log.error("Skipping quarter due to extraction error", quarter=quarter, error=error)
                file_result["quarters"][quarter] = {
                    "status": "error",
                    "detail": error,
                }
                continue

            if not plan_dicts:
                log.warning("No plans found for quarter", quarter=quarter)
                file_result["quarters"][quarter] = {"status": "no_plans_found", "plans": 0}
                continue

            try:
                plan_objects = [InsurancePlan(**p) for p in plan_dicts]
                log.info("Saving plans for quarter", quarter=quarter, plan_count=len(plan_objects))
                summary = await save_plans(db, plan_objects)

                file_result["quarters"][quarter] = {
                    "status": "success",
                    "plans": len(plan_objects),
                    **summary,
                }
                file_result["total_plans"] += len(plan_objects)
                file_result["inserted"] += summary["inserted"]
                file_result["updated_exact"] += summary["updated_exact"]
                file_result["updated_fuzzy"] += summary["updated_fuzzy"]
                log.info(
                    "Quarter saved",
                    quarter=quarter,
                    inserted=summary["inserted"],
                    updated_exact=summary["updated_exact"],
                    updated_fuzzy=summary["updated_fuzzy"],
                )

            except Exception as e:
                await db.rollback()
                log.error("DB save failed for quarter", quarter=quarter, error=str(e))
                file_result["quarters"][quarter] = {
                    "status": "error",
                    "detail": str(e),
                }

    file_result["status"] = "success" if file_result["total_plans"] > 0 else "no_plans_found"
    log.info(
        "File processing complete",
        status=file_result["status"],
        total_plans=file_result["total_plans"],
        inserted=file_result["inserted"],
        updated_exact=file_result["updated_exact"],
        updated_fuzzy=file_result["updated_fuzzy"],
    )
    return file_result


@router.post("/ingest")
async def ingest_pdfs(
        files: Annotated[List[UploadFile], File(description="Upload Insurance PDFs to ingest")],
        quarter: Optional[str] = Form(None, description="Override quarter (Q1-Q4). Leave blank to auto-detect."),
        api_key: str = Security(get_api_key),
):
    """
    Ingest one or more insurance PDFs in parallel. For each file:
    1. Upload PDF to OpenAI (once)
    2. Detect which quarters are present (or use quarter override)
    3. Extract all quarters in parallel
    4. Save plans to DB
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for '{file.filename}'. All files must be PDFs."
            )

    quarter_override = quarter.strip().upper() if quarter else None
    if quarter_override and quarter_override not in VALID_QUARTERS:
        raise HTTPException(status_code=400, detail=f"Invalid quarter '{quarter}'. Must be Q1, Q2, Q3, or Q4.")

    filenames = [f.filename for f in files]
    logger.info("Ingest request received", file_count=len(files), filenames=filenames, quarter_override=quarter_override)

    # Read all file contents first (UploadFile must be read in the request context)
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename, content))

    # Process all files in parallel
    logger.info("Starting parallel file processing", file_count=len(file_data))
    results_per_file = await asyncio.gather(
        *[_process_single_file(name, content, quarter_override) for name, content in file_data]
    )

    total_plans = sum(r.get("total_plans", 0) for r in results_per_file)
    logger.info(
        "Ingest complete",
        total_files=len(files),
        total_plans_ingested=total_plans,
    )
    return {
        "total_files": len(files),
        "total_plans_ingested": total_plans,
        "files": list(results_per_file),
    }
