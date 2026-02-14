import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from typing import Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from .service import extract_from_pdf, upload_pdf, detect_quarters
from .schemas import InsurancePlan
from src.database import get_db
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


@router.post("/ingest")
async def ingest_pdfs(
        files: Annotated[List[UploadFile], File(description="Upload Insurance PDFs to ingest")],
        api_key: str = Security(get_api_key),
        db: AsyncSession = Depends(get_db),
):
    """
    Ingest one or more insurance PDFs. For each file:
    1. Upload PDF to OpenAI (once)
    2. Detect which quarters are present (lightweight call)
    3. Extract plans quarter-by-quarter, saving each to DB before the next
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for '{file.filename}'. All files must be PDFs."
            )

    results_per_file = []

    for file in files:
        content = await file.read()
        filename = file.filename
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
            results_per_file.append(file_result)
            continue

        # 2. Detect which quarters exist in this file
        try:
            detected = await detect_quarters(file_id)
            file_result["detected_quarters"] = detected
        except Exception as e:
            file_result["status"] = "error"
            file_result["detail"] = f"Quarter detection failed: {str(e)}"
            results_per_file.append(file_result)
            continue

        # 3. Extract plans for each detected quarter sequentially
        for quarter in detected:
            try:
                plan_dicts = await extract_from_pdf(file_id, quarter)

                if not plan_dicts:
                    file_result["quarters"][quarter] = {"status": "no_plans_found", "plans": 0}
                    continue

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
        results_per_file.append(file_result)

    total_plans = sum(r.get("total_plans", 0) for r in results_per_file)
    return {
        "total_files": len(files),
        "total_plans_ingested": total_plans,
        "files": results_per_file,
    }
