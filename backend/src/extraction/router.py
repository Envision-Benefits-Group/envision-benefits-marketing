from datetime import datetime
from enum import Enum
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated, Optional
from .service import extract_from_pdf, process_excel_report  # <--- Updated name

router = APIRouter()

VALID_QUARTERS = {"Q1", "Q2", "Q3", "Q4"}


@router.post("/process-pdf")
async def process_pdf(
        file: Annotated[UploadFile, File(description="Upload the Insurance PDF")],
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

    filename = f"Insurance_Matrix_{quarter}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
