import os
import asyncio
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
from typing import Annotated, Optional, List
from .service import extract_from_pdf, process_excel_report

router = APIRouter()

VALID_QUARTERS = {"Q1", "Q2", "Q3", "Q4"}
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

@router.post("/process-pdf")
async def process_pdf(
        file: Annotated[UploadFile, File(description="Upload the Insurance PDF")],
        api_key: str = Security(get_api_key),
        quarter: Annotated[Optional[str], Form(description="Target Quarter (e.g., Q1, Q2, Q3, Q4)")] = None
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    if quarter:
        quarter = quarter.strip().upper()
        if quarter not in VALID_QUARTERS:
            raise HTTPException(status_code=400, detail=f"Invalid quarter '{quarter}'. Must be one of: Q1, Q2, Q3, Q4")
    else:
        quarter = f"Q{(datetime.now().month - 1) // 3 + 1}"
    content = await file.read()

    # 1. AI Extraction
    try:
        df = await extract_from_pdf(content, quarter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if df.empty:
        raise HTTPException(status_code=400, detail="No plans extracted.")

    # 2. Excel Generation (Using the class via service)
    excel_file = process_excel_report(df)

    carrier = "-".join(df['carrier'].unique()).replace(" ", "_")
    filename = f"Insurance-{carrier}-{quarter}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/process-pdfs")
async def process_pdfs(
        files: Annotated[List[UploadFile], File(description="Upload multiple Insurance PDFs")],
        api_key: str = Security(get_api_key),
        quarter: Annotated[Optional[str], Form(description="Target Quarter (e.g., Q1, Q2, Q3, Q4)")] = None
):
    """
    Process multiple PDF files in parallel and return a single combined Excel report.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    # Validate all files are PDFs
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for '{file.filename}'. All files must be PDFs."
            )

    # Validate/auto-detect quarter
    if quarter:
        quarter = quarter.strip().upper()
        if quarter not in VALID_QUARTERS:
            raise HTTPException(status_code=400, detail=f"Invalid quarter '{quarter}'. Must be one of: Q1, Q2, Q3, Q4")
    else:
        quarter = f"Q{(datetime.now().month - 1) // 3 + 1}"

    # Read all file contents
    file_contents = []
    for file in files:
        content = await file.read()
        file_contents.append((file.filename, content))

    # Process all PDFs in parallel
    async def extract_single(filename: str, content: bytes) -> pd.DataFrame:
        try:
            return await extract_from_pdf(content, quarter)
        except Exception as e:
            print(f"Error extracting from {filename}: {str(e)}")
            return pd.DataFrame()

    extraction_tasks = [
        extract_single(filename, content)
        for filename, content in file_contents
    ]

    results = await asyncio.gather(*extraction_tasks)

    # Combine all DataFrames
    combined_df = pd.concat([df for df in results if not df.empty], ignore_index=True)

    if combined_df.empty:
        raise HTTPException(status_code=400, detail="No plans extracted from any of the uploaded files.")

    # Generate single Excel report
    excel_file = process_excel_report(combined_df)

    carriers = "-".join(combined_df['carrier'].unique()).replace(" ", "_")
    filename = f"Insurance-{carriers}-{quarter}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
