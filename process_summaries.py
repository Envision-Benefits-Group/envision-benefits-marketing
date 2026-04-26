"""
Benefit Summary Batch Processor
Runs directly on EC2, bypasses Traefik entirely.
Calls OpenAI API to extract benefits and updates the database directly.
"""

import os
import sys
import json
import asyncio
import hashlib
from pathlib import Path
from io import BytesIO

# Add the backend to the path
sys.path.insert(0, '/home/ubuntu/envision-benefits-marketing/backend')

from openai import AsyncOpenAI
from pydantic import BaseModel
from difflib import SequenceMatcher
import psycopg2
from psycopg2.extras import RealDictCursor

# ── Config ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Try reading from .env file
    env_file = Path("/home/ubuntu/envision-benefits-marketing/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                OPENAI_API_KEY = line.split("=", 1)[1].strip().split("#")[0].strip()
                break

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": None,
}

# Try reading DB password from .env
env_file = Path("/home/ubuntu/envision-benefits-marketing/.env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("POSTGRES_PASSWORD="):
            DB_CONFIG["password"] = line.split("=", 1)[1].strip().split("#")[0].strip()

SUMMARY_DIRS = {
    "2025": [
        "/home/claude/summaries/2025_HMK_Summary",
        "/home/claude/summaries/2025_IHA_Summary",
        "/home/claude/summaries/2025_Univera_Summaries",
    ],
    "2026": [
        "/home/claude/summaries/2026_Summary_HMK",
        "/home/claude/summaries/2026_IHA_Summaries",
        "/home/claude/summaries/2026_Univera_Summaries",
        "/home/claude/summaries/2026_syr_summary_Excellus",
        "/home/claude/summaries/2026_Utica_Excellus_Summary",
        "/home/claude/summaries/2026_Roch_Excellus_summary",
    ],
}

BENEFIT_FIELDS = [
    "wellness_benefit", "deductible_in_ee", "deductible_in_fam",
    "in_network_deductible_type", "coinsurance_in",
    "oop_max_in_ee", "oop_max_in_fam", "in_network_oop_type",
    "pcp_copay", "specialist_copay", "inpatient_hospital", "outpatient_facility",
    "emergency_room", "urgent_care",
    "deductible_oon_ee", "deductible_oon_fam", "out_network_deductible_type",
    "coinsurance_oon", "oop_max_oon_ee", "oop_max_oon_fam", "out_network_oop_type",
    "rx_generic", "rx_preferred_brand", "rx_non_preferred_brand",
    "hsa_qualified", "creditable_coverage", "dependent_coverage",
]

# ── Pydantic models ───────────────────────────────────────────────────────────
class BenefitSummary(BaseModel):
    carrier: str = ""
    plan_name: str = ""
    year: int = 0
    wellness_benefit: str = ""
    deductible_in_ee: str = ""
    deductible_in_fam: str = ""
    in_network_deductible_type: str = "E"
    coinsurance_in: str = ""
    oop_max_in_ee: str = ""
    oop_max_in_fam: str = ""
    in_network_oop_type: str = "E"
    pcp_copay: str = ""
    specialist_copay: str = ""
    inpatient_hospital: str = ""
    outpatient_facility: str = ""
    emergency_room: str = ""
    urgent_care: str = ""
    deductible_oon_ee: str = ""
    deductible_oon_fam: str = ""
    out_network_deductible_type: str = "E"
    coinsurance_oon: str = ""
    oop_max_oon_ee: str = ""
    oop_max_oon_fam: str = ""
    out_network_oop_type: str = "E"
    rx_generic: str = ""
    rx_preferred_brand: str = ""
    rx_non_preferred_brand: str = ""
    hsa_qualified: str = ""
    creditable_coverage: str = ""
    dependent_coverage: str = "Age 26"
    benefit_allowance_ee: str = ""
    benefit_allowance_fam: str = ""

class BenefitWrapper(BaseModel):
    plan: BenefitSummary

# ── OpenAI extraction ─────────────────────────────────────────────────────────
async def extract_benefits(client: AsyncOpenAI, pdf_path: str, year_hint: int) -> BenefitSummary | None:
    system_rules = f"""
You are a specialized health insurance benefit extractor.
Extract benefit details ONLY — do NOT extract premium rates.
The year for these plans is approximately {year_hint}.

Extract the following fields:
- carrier: Normalize to "IHA", "Univera", "Excellus", or "Highmark"
- plan_name: Clean name without carrier prefix or HIOS IDs
- year: Effective year from document dates (use {year_hint} if not clear)
- wellness_benefit, deductible_in_ee, deductible_in_fam, in_network_deductible_type (E=Embedded, T=True Family)
- coinsurance_in, oop_max_in_ee, oop_max_in_fam, in_network_oop_type
- pcp_copay, specialist_copay, inpatient_hospital
- outpatient_facility: ASC cost ONLY — if both Hospital and ASC listed separately, use only ASC cost
- emergency_room, urgent_care
- deductible_oon_ee, deductible_oon_fam, out_network_deductible_type
- coinsurance_oon, oop_max_oon_ee, oop_max_oon_fam, out_network_oop_type
- rx_generic, rx_preferred_brand, rx_non_preferred_brand
- hsa_qualified, creditable_coverage (from page 4 for IHA — "Creditable Coverage" or "Non-Creditable Coverage")
- dependent_coverage: standardize to "Age 26"
- benefit_allowance_ee, benefit_allowance_fam: IHA Activate plans only — First Dollar Coverage amounts

IHA ACTIVATE: Extract benefit_allowance_ee/fam. Format deductible_in_ee as:
"Allowance: $X / $Y\\nDeductible: $X / $Y (Embedded)"

VERBIAGE: Convert "X after deductible" to "Deductible then X"
FORMATTING: Remove "FS" from coinsurance
"""

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    try:
        uploaded = await client.files.create(
            file=("summary.pdf", BytesIO(pdf_bytes), "application/pdf"),
            purpose="user_data",
        )

        resp = await client.responses.parse(
            model="gpt-4o",
            instructions=system_rules,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_file", "file_id": uploaded.id},
                    {"type": "input_text", "text": "Extract all benefit details from this benefit summary PDF."},
                ],
            }],
            text_format=BenefitWrapper,
        )

        # Clean up uploaded file
        try:
            await client.files.delete(uploaded.id)
        except:
            pass

        if resp.output_parsed and resp.output_parsed.plan:
            return resp.output_parsed.plan
        return None

    except Exception as e:
        print(f"  ✗ OpenAI error: {e}")
        return None

# ── Database update ───────────────────────────────────────────────────────────
def update_db(benefit: BenefitSummary, year_override: int) -> int:
    year = year_override or benefit.year

    # Build allowance deductible display
    if benefit.benefit_allowance_ee and benefit.benefit_allowance_fam:
        ded_type = "Embedded" if benefit.in_network_deductible_type == "E" else "True Family"
        benefit.deductible_in_ee = f"Allowance: {benefit.benefit_allowance_ee} / {benefit.benefit_allowance_fam}\nDeductible: {benefit.deductible_in_ee} / {benefit.deductible_in_fam} ({ded_type})"
        benefit.deductible_in_fam = benefit.deductible_in_ee

    # Build rx_display
    parts = []
    if benefit.rx_generic: parts.append(f"Generic: {benefit.rx_generic}")
    if benefit.rx_preferred_brand: parts.append(f"Preferred: {benefit.rx_preferred_brand}")
    if benefit.rx_non_preferred_brand: parts.append(f"Non-Preferred: {benefit.rx_non_preferred_brand}")
    rx_display = " / ".join(parts)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Find matching plans by carrier + year, fuzzy match on name
        cur.execute(
            "SELECT plan_id, plan_name FROM plans WHERE carrier = %s AND year = %s",
            (benefit.carrier, year)
        )
        candidates = cur.fetchall()

        updated = 0
        incoming_name = benefit.plan_name.strip().lower()

        for candidate in candidates:
            ratio = SequenceMatcher(None, candidate["plan_name"].strip().lower(), incoming_name).ratio()
            if ratio >= 0.75:
                plan_id = candidate["plan_id"]

                # Check if medical_plan_details exists
                cur.execute("SELECT plan_id FROM medical_plan_details WHERE plan_id = %s", (plan_id,))
                exists = cur.fetchone()

                field_updates = {f: getattr(benefit, f, "") for f in BENEFIT_FIELDS if getattr(benefit, f, "")}

                if exists:
                    if field_updates:
                        set_clause = ", ".join(f"{k} = %s" for k in field_updates)
                        values = list(field_updates.values()) + [plan_id]
                        cur.execute(f"UPDATE medical_plan_details SET {set_clause} WHERE plan_id = %s", values)
                else:
                    if field_updates:
                        cols = ", ".join(["plan_id"] + list(field_updates.keys()))
                        placeholders = ", ".join(["%s"] * (1 + len(field_updates)))
                        values = [plan_id] + list(field_updates.values())
                        cur.execute(f"INSERT INTO medical_plan_details ({cols}) VALUES ({placeholders})", values)

                updated += 1

        conn.commit()
        cur.close()
        conn.close()
        return updated

    except Exception as e:
        print(f"  ✗ DB error: {e}")
        return 0

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    if not OPENAI_API_KEY:
        print("ERROR: Could not find OPENAI_API_KEY")
        sys.exit(1)

    print(f"OpenAI key found: {OPENAI_API_KEY[:8]}...")
    print(f"DB config: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print()

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    total_processed = 0
    total_updated = 0
    total_failed = 0

    for year_str, dirs in SUMMARY_DIRS.items():
        year_int = int(year_str)
        for directory in dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                print(f"Skipping missing directory: {directory}")
                continue

            pdfs = sorted(dir_path.glob("*.pdf"))
            if not pdfs:
                continue

            print(f"\n📁 {dir_path.name} ({len(pdfs)} files, year={year_int})")
            print("─" * 60)

            for pdf in pdfs:
                print(f"  Processing: {pdf.name}", end="", flush=True)
                benefit = await extract_benefits(client, str(pdf), year_int)

                if not benefit or not benefit.plan_name:
                    print(" → ✗ No data extracted")
                    total_failed += 1
                    continue

                n_updated = update_db(benefit, year_int)
                total_processed += 1

                if n_updated > 0:
                    print(f" → ✓ Updated {n_updated} plan(s) [{benefit.carrier}: {benefit.plan_name}]")
                    total_updated += n_updated
                else:
                    print(f" → ⚠ No DB match [{benefit.carrier}: {benefit.plan_name}]")
                    total_failed += 1

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"COMPLETE: {total_processed} processed, {total_updated} DB records updated, {total_failed} failures")

if __name__ == "__main__":
    asyncio.run(main())
