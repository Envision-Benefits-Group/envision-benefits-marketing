import os
from io import BytesIO
from openai import AsyncOpenAI
from fastapi import HTTPException

from .schemas import PlanList, DetectedQuarters

API_KEY = os.getenv("OPENAI_API_KEY")


def get_client() -> AsyncOpenAI:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY_V2 is not set.")
    return AsyncOpenAI(api_key=API_KEY)


async def upload_pdf(file_content: bytes) -> str:
    """Upload a PDF and return the file_id for reuse across quarter extractions."""
    client = get_client()

    if not file_content or not file_content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file does not appear to be a valid PDF.")

    uploaded = await client.files.create(
        file=("rates.pdf", BytesIO(file_content), "application/pdf"),
        purpose="user_data",
    )
    return uploaded.id


async def detect_quarters(file_id: str) -> list[str]:
    """
    Lightweight call to detect which quarters are present in the PDF.
    Returns e.g. ["Q1", "Q2"] or ["Q1", "Q2", "Q3", "Q4"].
    """
    client = get_client()

    try:
        resp = await client.responses.parse(
            model="gpt-5.2",
            reasoning={"effort": "low"},
            instructions=(
                "You are analyzing an insurance document. "
                "Identify which quarters (Q1, Q2, Q3, Q4) have rate data in this document. "
                "Only include quarters that have actual rate tables or pricing. "
                "If the document has rates with no quarter distinction, return ['Q1']."
            ),
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_file", "file_id": file_id},
                        {"type": "input_text", "text": "Which quarters have rate data in this document?"},
                    ],
                }
            ],
            text_format=DetectedQuarters,
        )

        result: DetectedQuarters | None = resp.output_parsed
        if not result or not result.quarters:
            return ["Q1"]

        # Normalize and validate
        valid = {"Q1", "Q2", "Q3", "Q4"}
        quarters = [q.strip().upper() for q in result.quarters if q.strip().upper() in valid]
        return sorted(quarters) if quarters else ["Q1"]

    except Exception as e:
        print(f"Quarter detection error: {str(e)}")
        # Fallback: assume all 4 quarters
        return ["Q1", "Q2", "Q3", "Q4"]


async def extract_from_pdf(file_id: str, target_quarter: str) -> list:
    """
    Extract plan data from a PDF for a single quarter.
    Accepts a pre-uploaded file_id to avoid re-uploading for each quarter.
    Returns a list of InsurancePlan dicts.
    """
    client = get_client()

    system_rules = f"""
You are a specialized health insurance data extractor.
Extract ALL health insurance plans from the document for {target_quarter} ONLY.

STRICT COMPLIANCE RULES:
1. QUARTER: Extract ONLY the rates for {target_quarter}. Set the quarter field to "{target_quarter}" for every plan.
2. DEDUCTIBLE TYPE: Set in_network_deductible_type and out_network_deductible_type to 'T' for True Family or 'E' for Embedded.
3. OOP TYPE: Set in_network_oop_type and out_network_oop_type to 'T' for True Family or 'E' for Embedded.
4. OOP MAX: Extract OOP Max for both In-Network (oop_max_in_ee, oop_max_in_fam) and Out-of-Network (oop_max_oon_ee, oop_max_oon_fam).
5. FORMATTING: Remove 'FS' from coinsurance strings.
6. VERBIAGE: Convert all cost descriptions like '$ after deductible' to 'Deductible then $'.
7. RATES: Use ONLY the 'Dependent age 26' tables.
8. YEAR: Extract the effective year of the plan rates from the document (e.g. 2025, 2026). Look for phrases like "Effective Date", "Plan Year", or date ranges indicating the coverage period.
9. If there are no rates for {target_quarter} in this document, return an empty plans list.
10. SKIP: Do NOT extract Vision or Dental plans. Only extract Medical/Health insurance plans.
11. CARRIER NAME: Normalize the carrier name to one of these exact values:
    - "IHA" (for Independent Health Association / Independent Health)
    - "Univera" (for Univera Healthcare / Univera Health)
    - "Excellus" (for Excellus BlueCross BlueShield / Excellus BCBS)
    - "Highmark" (for Highmark Blue Cross Blue Shield / Highmark BCBS)
    If the carrier does not match any of the above, use the name as it appears in the document.
12. PLAN NAME NORMALIZATION: Clean up and normalize plan names. Remove carrier prefixes, HIOS IDs, plan IDs, parenthetical identifiers, and redundant suffixes. Use short, consistent names.
    Examples:
    - "Highmark Blue Cross Blue Shield Platinum Classic" → "Platinum Classic"
    - "Highmark Platinum POS Plus" → "Platinum POS Plus"
    - "Gold POS 7100 (HIOS ID: 12345)" → "Gold POS 7100"
    - "IHA FlexFit Platinum" → "FlexFit Platinum"
    - "Independent Health iDirect Gold Copay" → "iDirect Gold Copay"
    - "iDirect Gold Copay Option 3" → "iDirect Gold Copay Option 3"
    - "Passport Plan National Gold HSAQ" → "Passport Plan National Gold HSAQ"
    - "Passport Plan Local Platinum" → "Passport Plan Local Platinum"
    - "Univera Healthy New York EPO (HIOS ID/Plan ID 12345)" → "Healthy New York"
    - "Healthy New York EPO" and "Healthy New York EPO (HIOS ID/Plan ID ...)" are the SAME plan — extract only ONCE.
    - "WNY Gold Healthy NY (Gold Standard)" → "WNY Gold Healthy NY (Gold Standard)"
    - "Standard Healthy NY Gold" → "Standard Healthy NY Gold"
    - "Univera Access Plus Gold 1" → "Access Plus Gold 1"
    - "Excellus Silver Classic" → "Silver Classic"
    Rules:
    - Strip carrier name prefix from plan_name (the carrier is already in the carrier field)
    - Remove HIOS ID, Plan ID, or any parenthetical ID suffixes
    - If two plans have identical rates and benefits but slightly different names (e.g. one has an ID suffix), they are the SAME plan — extract only once
    - Keep metal tier (Platinum/Gold/Silver/Bronze), network type (POS/PPO/EPO), and plan variant identifiers (Classic, Plus, EX, Apex, HSAQ, Option 2, etc.)
"""

    try:
        resp = await client.responses.parse(
            model="gpt-5.2",
            reasoning={"effort": "high"},
            instructions=system_rules,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_file", "file_id": file_id},
                        {
                            "type": "input_text",
                            "text": f"Extract all insurance plan data from this document for {target_quarter} only.",
                        },
                    ],
                }
            ],
            text_format=PlanList,
        )

        structured: PlanList | None = resp.output_parsed
        if not structured or not structured.plans:
            return []

        return [plan.model_dump() for plan in structured.plans]

    except Exception as e:
        print(f"GPT Extraction Error ({target_quarter}): {str(e)}")
        raise
