import os
import pandas as pd
from io import BytesIO
from openai import AsyncOpenAI
from fastapi import HTTPException

from backend.src.extraction.schemas import PlanList
from backend.src.extraction.excel_generator import ExcelReportGenerator

API_KEY = os.getenv("OPENAI_API_KEY")


def get_client() -> AsyncOpenAI:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY_V2 is not set.")
    return AsyncOpenAI(api_key=API_KEY)


async def extract_from_pdf(file_content: bytes, target_quarter: str) -> pd.DataFrame:
    """
    Extract plan data from a PDF using OpenAI Responses API.
    The PDF is uploaded first and referenced by file_id (recommended approach).
    """
    client = get_client()

    # Basic sanity check
    if not file_content or not file_content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file does not appear to be a valid PDF.")

    system_rules = f"""
You are a specialized health insurance data extractor.
Extract all health insurance plans for {target_quarter}.

STRICT COMPLIANCE RULES:
1. TARGET QUARTER: Extract ONLY the rates for {target_quarter}.
2. DEDUCTIBLE TYPE: Set in_network_deductible_type and out_network_deductible_type to 'T' for True Family or 'E' for Embedded.
3. FORMATTING: Remove 'FS' from coinsurance strings.
4. VERBIAGE: Convert all cost descriptions like '$ after deductible' to 'Deductible then $'.
5. RATES: Use ONLY the 'Dependent age 26' tables.
"""

    try:
        # 1) Upload the PDF (Gemini from_bytes equivalent)
        uploaded = await client.files.create(
            file=("rates.pdf", BytesIO(file_content), "application/pdf"),
            purpose="user_data",
        )

        # 2) Reference the uploaded file in the model request
        resp = await client.responses.parse(
            model="gpt-5-mini",
                reasoning={"effort": "medium"},
            instructions=system_rules,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_file", "file_id": uploaded.id},
                        {
                            "type": "input_text",
                            "text": f"Extract data from this insurance document for {target_quarter}.",
                        },
                    ],
                }
            ],
            text_format=PlanList,
        )

        structured: PlanList | None = resp.output_parsed
        if not structured or not structured.plans:
            return pd.DataFrame()

        return pd.DataFrame([plan.model_dump() for plan in structured.plans])

    except Exception as e:
        print(f"GPT Extraction Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Extraction failed: {str(e)}")


def process_excel_report(df: pd.DataFrame):
    if df.empty:
        raise HTTPException(status_code=400, detail="No data extracted to generate report.")
    generator = ExcelReportGenerator()
    return generator.generate(df)
