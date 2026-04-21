import os
import structlog
from io import BytesIO
from openai import AsyncOpenAI
from fastapi import HTTPException

from .schemas import PlanList, DetectedQuarters

logger = structlog.get_logger(__name__)

API_KEY = os.getenv("OPENAI_API_KEY")

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if not API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set.")
    if _client is None:
        _client = AsyncOpenAI(api_key=API_KEY)
    return _client


async def upload_pdf(file_content: bytes) -> str:
    """Upload a PDF and return the file_id for reuse across quarter extractions."""
    client = get_client()

    if not file_content or not file_content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file does not appear to be a valid PDF.")

    logger.info("Uploading PDF to OpenAI", file_size_bytes=len(file_content))
    try:
        uploaded = await client.files.create(
            file=("rates.pdf", BytesIO(file_content), "application/pdf"),
            purpose="user_data",
        )
        logger.info("PDF uploaded successfully", file_id=uploaded.id)
        return uploaded.id
    except Exception as e:
        logger.error("PDF upload to OpenAI failed", error=str(e))
        raise


async def detect_quarters(file_id: str) -> list[str]:
    """
    Lightweight call to detect which quarters are present in the PDF.
    Returns e.g. ["Q1", "Q2"] or ["Q1", "Q2", "Q3", "Q4"].
    """
    client = get_client()
    logger.info("Detecting quarters in document", file_id=file_id)

    try:
        resp = await client.responses.parse(
            model="gpt-5-mini",
            reasoning = {"effort": "high"},
            instructions=(
                "You are analyzing an insurance document. "
                "Identify which quarters (Q1, Q2, Q3, Q4) have rate data in this document. "
                "Map effective date ranges to quarters: Jan–Mar = Q1, Apr–Jun = Q2, Jul–Sep = Q3, Oct–Dec = Q4. "
                "Examples: 'Quote Effective: 10/01/2025 - 12/31/2025' → Q4. "
                "'Effective: 01/01/2026 - 03/31/2026' → Q1. "
                "'Effective: 04/01/2025 - 06/30/2025' → Q2. "
                "If the document contains multiple distinct quarterly rate tables, return all applicable quarters. "
                "If the document spans a full calendar year (Jan–Dec) or has no date information at all, return ['Q1', 'Q2', 'Q3', 'Q4']. "
                "Only include quarters that have actual rate tables or pricing."
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
            logger.warning("Quarter detection returned empty result, defaulting to Q1", file_id=file_id)
            return ["Q1"]

        # Normalize and validate
        valid = {"Q1", "Q2", "Q3", "Q4"}
        quarters = [q.strip().upper() for q in result.quarters if q.strip().upper() in valid]
        final = sorted(quarters) if quarters else ["Q1"]
        logger.info("Quarters detected", file_id=file_id, quarters=final)
        return final

    except Exception as e:
        logger.error(
            "Quarter detection failed, falling back to all quarters",
            file_id=file_id,
            error=str(e),
        )
        return ["Q1", "Q2", "Q3", "Q4"]


async def extract_from_pdf(file_id: str, target_quarter: str) -> list:
    """
    Extract plan data from a PDF for a single quarter.
    Accepts a pre-uploaded file_id to avoid re-uploading for each quarter.
    Returns a list of InsurancePlan dicts.
    """
    client = get_client()
    logger.info("Starting plan extraction", file_id=file_id, quarter=target_quarter)

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
7. RATES: When the document contains multiple rate tables segmented by dependent age (e.g. "Dependent age 26" vs "Dependent age 29"), use ONLY the 'Dependent age 26' table. If the document has a single rate table with no age-tier distinction (such as HealthyNY or other single-table plans), use that table as-is. Never skip a plan solely because it lacks an age-labeled table.
   RATE LABEL MAPPING: Map these alternative labels to the correct fields — "Single" or "EE Only" or "Employee Only" → ee_only; "Subscriber & Spouse" or "EE + Spouse" or "Employee + Spouse" → ee_spouse; "Subscriber & Child(ren)" or "EE + Child(ren)" or "Employee + Children" → ee_children; "Family" → family.
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

13. IHA ACTIVATE PLANS — BENEFIT ALLOWANCE (FIRST DOLLAR COVERAGE):
    IHA "Activate" plans include a Benefit Allowance that applies BEFORE the deductible. This may appear as "First Dollar Coverage", "Benefit Allowance", or a dollar amount shown above the deductible in the benefit summary.
    - Extract the allowance amounts into the fields: benefit_allowance_ee and benefit_allowance_fam.
    - Example: If the summary shows "Allowance: $750 / $1,500" before the deductible, set benefit_allowance_ee="$750" and benefit_allowance_fam="$1,500".
    - The deductible_display field should then be formatted as:
      "Allowance: $750 / $1,500\\nDeductible: $1,500 / $3,000 (Embedded)"
    - All benefit lines for Activate plans (coinsurance, copays, etc.) apply AFTER the allowance is exhausted, then the deductible applies. Extract them exactly as stated in the summary — do not assume they are incorrect.
    - If no allowance is present, leave benefit_allowance_ee and benefit_allowance_fam empty.

14. OUTPATIENT SURGICAL — ASC ONLY:
    When extracting the Outpatient Surgical benefit (outpatient_facility field):
    - If the plan lists BOTH a hospital outpatient cost AND an Ambulatory Surgery Center (ASC) cost separately, extract ONLY the ASC cost.
    - ASC is also called "Ambulatory Surgical Center", "Ambulatory Surgery Center", or labeled "ASC" in the benefit summary.
    - Example: If summary shows "Hospital: Deductible then $375 / ASC: Deductible then $325", set outpatient_facility = "Deductible then $325".
    - Example: If summary shows "ASC Deductible then 25%; Hospital Deductible then 25%", set outpatient_facility = "Deductible then 25%".
    - If only one outpatient surgical cost is listed (no ASC/Hospital split), use that single value as-is.

15. PRESCRIPTION (Rx) — SINGLE LINE FORMAT:
    Combine all Rx tier information into a single consolidated string for the rx_display field.
    Format: "Generic: $X / Preferred: $X / Non-Preferred: $X"
    Example: "Generic: $10 Copay / Preferred: $40 Copay / Non-Preferred: $100 Copay"
    Also still populate the individual fields rx_generic, rx_preferred_brand, rx_non_preferred_brand separately.
    For plans with deductible-first Rx: "Generic: Deductible then $10 / Preferred: Deductible then 25% / Non-Preferred: Deductible then 50%"

16. MEDICARE PART D:
    IHA plan summaries include a Medicare Part D / Creditable Coverage notice, typically on page 4 of the benefit summary.
    - Extract the Medicare Part D creditable coverage status into the creditable_coverage field.
    - If the summary states the plan IS creditable coverage for Medicare Part D, set creditable_coverage = "Creditable Coverage".
    - If it states the plan is NOT creditable, set creditable_coverage = "Non-Creditable Coverage".
    - If not stated or not found, set creditable_coverage = "Not stated".
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
            logger.warning("No plans extracted from document", file_id=file_id, quarter=target_quarter)
            return []

        plan_list = [plan.model_dump() for plan in structured.plans]
        logger.info(
            "Plan extraction complete",
            file_id=file_id,
            quarter=target_quarter,
            plan_count=len(plan_list),
        )
        return plan_list

    except Exception as e:
        logger.error(
            "GPT extraction failed",
            file_id=file_id,
            quarter=target_quarter,
            error=str(e),
        )
        raise
