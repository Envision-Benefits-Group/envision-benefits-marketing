import os
import json
import pandas as pd
from google import genai
from google.genai import types
from fastapi import HTTPException

# Import the new class and schemas
from .schemas import PlanList
from .excel_generator import ExcelReportGenerator # <--- NEW IMPORT

API_KEY = os.getenv("GEMINI_API_KEY")

def get_client():
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")
    return genai.Client(api_key=API_KEY)


async def extract_from_pdf(file_content: bytes, target_quarter: str) -> pd.DataFrame:
    client = get_client()
    prompt = f"""
    Extract all health insurance plans for {target_quarter}.
    STRICT CLIENT RULES:
    1. TARGET QUARTER: Extract ONLY the rates for {target_quarter}.
    2. DEDUCTIBLE TYPE: Set in_network_deductible_type and out_network_deductible_type to 'T' for True Family or 'E' for Embedded.
    3. FORMATTING: Remove 'FS' from coinsurance.
    4. VERBIAGE: Convert all cost descriptions like '$ after deductible' to 'Deductible then $'.
    5. RATES: Use ONLY the 'Dependent age 26' tables.
    """

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=PlanList.model_json_schema(),
        thinking_config=types.ThinkingConfig(thinking_level="high")
    )

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                types.Part.from_bytes(data=file_content, mime_type="application/pdf"),
                prompt
            ],
            config=config
        )
        data = json.loads(response.text)
        return pd.DataFrame(data.get("plans", []))

    except Exception as e:
        print(f"Extraction Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Extraction failed: {str(e)}")


def process_excel_report(df: pd.DataFrame):
    """
    Delegates the Excel creation to the dedicated generator class.
    """
    generator = ExcelReportGenerator()
    return generator.generate(df)
