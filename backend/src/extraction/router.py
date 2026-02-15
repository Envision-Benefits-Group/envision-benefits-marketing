import asyncio
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Annotated, List
from .service import extract_from_pdf, upload_pdf, detect_quarters
from .schemas import InsurancePlan
from src.database import AsyncSessionLocal
from src.plans.repository import save_plans

router = APIRouter()

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


async def _process_single_file(filename: str, content: bytes) -> dict:
    """
    Process a single PDF file: upload, detect quarters, extract plans
    per quarter in parallel, then save to DB sequentially.
    """
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
        file_result["status"] = "error"
        file_result["detail"] = f"Upload failed: {str(e)}"
        return file_result

    # 2. Detect which quarters exist
    try:
        detected = await detect_quarters(file_id)
        file_result["detected_quarters"] = detected
    except Exception as e:
        file_result["status"] = "error"
        file_result["detail"] = f"Quarter detection failed: {str(e)}"
        return file_result

    # 3. Extract all quarters in parallel (AI calls are the bottleneck)
    async def _extract_quarter(quarter: str):
        try:
            plan_dicts = await extract_from_pdf(file_id, quarter)
            return quarter, plan_dicts, None
        except Exception as e:
            return quarter, None, str(e)

    extraction_results = await asyncio.gather(
        *[_extract_quarter(q) for q in detected]
    )

    # 4. Save to DB sequentially (own session per file to avoid conflicts)
    async with AsyncSessionLocal() as db:
        for quarter, plan_dicts, error in extraction_results:
            if error:
                file_result["quarters"][quarter] = {
                    "status": "error",
                    "detail": error,
                }
                continue

            if not plan_dicts:
                file_result["quarters"][quarter] = {"status": "no_plans_found", "plans": 0}
                continue

            try:
                plan_objects = [InsurancePlan(**p) for p in plan_dicts]
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

            except Exception as e:
                await db.rollback()
                file_result["quarters"][quarter] = {
                    "status": "error",
                    "detail": str(e),
                }

    file_result["status"] = "success" if file_result["total_plans"] > 0 else "no_plans_found"
    return file_result


@router.post("/ingest")
async def ingest_pdfs(
        files: Annotated[List[UploadFile], File(description="Upload Insurance PDFs to ingest")],
        api_key: str = Security(get_api_key),
):
    """
    Ingest one or more insurance PDFs in parallel. For each file:
    1. Upload PDF to OpenAI (once)
    2. Detect which quarters are present (lightweight call)
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

    # Read all file contents first (UploadFile must be read in the request context)
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename, content))

    # Process all files in parallel
    results_per_file = await asyncio.gather(
        *[_process_single_file(name, content) for name, content in file_data]
    )

    total_plans = sum(r.get("total_plans", 0) for r in results_per_file)
    return {
        "total_files": len(files),
        "total_plans_ingested": total_plans,
        "files": list(results_per_file),
    }
