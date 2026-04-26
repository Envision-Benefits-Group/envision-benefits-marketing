import asyncio
import os
import structlog
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Security, status, BackgroundTasks
from fastapi.security import APIKeyHeader
from typing import Annotated, List, Optional
from .service import extract_from_pdf, upload_pdf, detect_quarters, extract_benefits_from_pdf
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
        background_tasks: BackgroundTasks,
        files: Annotated[List[UploadFile], File(description="Upload Insurance PDFs to ingest")],
        quarter: Optional[str] = Form(None, description="Override quarter (Q1-Q4). Leave blank to auto-detect."),
        api_key: str = Security(get_api_key),
):
    """
    Ingest one or more insurance PDFs. Returns immediately and processes in background.
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

    # Read all file contents immediately (must be done in request context)
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename, content))

    filenames = [f[0] for f in file_data]
    logger.info("Ingest request received — processing in background", file_count=len(file_data), filenames=filenames)

    # Process in background so browser doesn't time out
    async def run_background():
        results = await asyncio.gather(
            *[_process_single_file(name, content, quarter_override) for name, content in file_data]
        )
        total_plans = sum(r.get("total_plans", 0) for r in results)
        logger.info("Background ingest complete", total_files=len(file_data), total_plans_ingested=total_plans)

    background_tasks.add_task(run_background)

    return {
        "status": "processing",
        "message": f"Processing {len(file_data)} file(s) in the background. Check Plan Data tab in 1-2 minutes.",
        "total_files": len(file_data),
        "filenames": filenames,
    }


@router.post("/ingest-benefits")
async def ingest_benefit_summaries(
        files: Annotated[List[UploadFile], File(description="Upload IHA Benefit Summary PDFs")],
        year: Optional[str] = Form(None, description="Plan year (e.g. 2025 or 2026)"),
        api_key: str = Security(get_api_key),
):
    """
    Ingest benefit summary PDFs and update benefit fields on existing plan records.
    Matches plans by carrier + plan_name + year, updates benefit fields across ALL quarters.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    year_int = int(year) if year else None

    results = []

    for file in files:
        filename = file.filename
        log = logger.bind(filename=filename)
        content = await file.read()

        try:
            file_id = await upload_pdf(content)
        except Exception as e:
            results.append({"file": filename, "status": "error", "detail": f"Upload failed: {str(e)}"})
            continue

        try:
            benefit_data = await extract_benefits_from_pdf(file_id)
        except Exception as e:
            results.append({"file": filename, "status": "error", "detail": f"Extraction failed: {str(e)}"})
            continue

        if not benefit_data:
            results.append({"file": filename, "status": "no_data_found"})
            continue

        carrier = benefit_data.get("carrier")
        plan_name = benefit_data.get("plan_name")
        extracted_year = year_int or benefit_data.get("year")

        # Build benefit allowance deductible display if present
        allowance_ee = benefit_data.get("benefit_allowance_ee", "")
        allowance_fam = benefit_data.get("benefit_allowance_fam", "")
        ded_ee = benefit_data.get("deductible_in_ee", "")
        ded_fam = benefit_data.get("deductible_in_fam", "")
        ded_type = benefit_data.get("in_network_deductible_type", "E")
        type_label = "Embedded" if ded_type == "E" else "True Family"

        if allowance_ee and allowance_fam:
            benefit_data["deductible_in_ee"] = f"Allowance: {allowance_ee} / {allowance_fam}\nDeductible: {ded_ee} / {ded_fam} ({type_label})"
            benefit_data["deductible_in_fam"] = benefit_data["deductible_in_ee"]

        # Build rx_display consolidated field
        rx_g = benefit_data.get("rx_generic", "")
        rx_p = benefit_data.get("rx_preferred_brand", "")
        rx_np = benefit_data.get("rx_non_preferred_brand", "")
        rx_parts = []
        if rx_g: rx_parts.append(f"Generic: {rx_g}")
        if rx_p: rx_parts.append(f"Preferred: {rx_p}")
        if rx_np: rx_parts.append(f"Non-Preferred: {rx_np}")
        benefit_data["rx_display"] = " / ".join(rx_parts)

        # Find matching plans in DB across ALL quarters and update benefit fields
        from difflib import SequenceMatcher
        from src.plans.models import Plan, MedicalPlanDetails
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

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

        updated_count = 0
        async with AsyncSessionLocal() as db:
            # Find all plans for this carrier + year across ALL quarters
            stmt = (
                select(Plan)
                .options(selectinload(Plan.medical_details))
                .where(Plan.carrier == carrier, Plan.year == extracted_year)
            )
            result = await db.execute(stmt)
            candidates = result.scalars().all()

            incoming_name = plan_name.strip().lower()
            for candidate in candidates:
                candidate_name = candidate.plan_name.strip().lower()
                ratio = SequenceMatcher(None, candidate_name, incoming_name).ratio()
                if ratio >= 0.75:
                    log.info("Updating benefits for plan", plan_name=candidate.plan_name, quarter=candidate.quarter, ratio=round(ratio, 3))
                    if candidate.medical_details:
                        for field in BENEFIT_FIELDS:
                            if field in benefit_data and benefit_data[field]:
                                setattr(candidate.medical_details, field, benefit_data[field])
                    else:
                        details = MedicalPlanDetails(plan_id=candidate.plan_id)
                        for field in BENEFIT_FIELDS:
                            if field in benefit_data and benefit_data[field]:
                                setattr(details, field, benefit_data[field])
                        db.add(details)
                    updated_count += 1

            await db.commit()

        results.append({
            "file": filename,
            "status": "success" if updated_count > 0 else "no_match",
            "carrier": carrier,
            "plan_name": plan_name,
            "year": extracted_year,
            "plans_updated": updated_count,
        })
        log.info("Benefit ingest complete", carrier=carrier, plan_name=plan_name, plans_updated=updated_count)

    return {
        "total_files": len(files),
        "files": results,
    }
    """
    Ingest benefit summary PDFs and update benefit fields on existing plan records.
    Matches plans by carrier + plan_name + year + quarter, updates only benefit fields.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    year_int = int(year) if year else None
    quarter_override = quarter.strip().upper() if quarter else None

    results = []

    for file in files:
        filename = file.filename
        log = logger.bind(filename=filename)
        content = await file.read()

        try:
            file_id = await upload_pdf(content)
        except Exception as e:
            results.append({"file": filename, "status": "error", "detail": f"Upload failed: {str(e)}"})
            continue

        try:
            benefit_data = await extract_benefits_from_pdf(file_id)
        except Exception as e:
            results.append({"file": filename, "status": "error", "detail": f"Extraction failed: {str(e)}"})
            continue

        if not benefit_data:
            results.append({"file": filename, "status": "no_data_found"})
            continue

        carrier = benefit_data.get("carrier")
        plan_name = benefit_data.get("plan_name")
        extracted_year = year_int or benefit_data.get("year")
        q = quarter_override or "Q1"

        # Build benefit allowance deductible display if present
        allowance_ee = benefit_data.get("benefit_allowance_ee", "")
        allowance_fam = benefit_data.get("benefit_allowance_fam", "")
        ded_ee = benefit_data.get("deductible_in_ee", "")
        ded_fam = benefit_data.get("deductible_in_fam", "")
        ded_type = benefit_data.get("in_network_deductible_type", "E")
        type_label = "Embedded" if ded_type == "E" else "True Family"

        if allowance_ee and allowance_fam:
            benefit_data["deductible_in_ee"] = f"Allowance: {allowance_ee} / {allowance_fam}\nDeductible: {ded_ee} / {ded_fam} ({type_label})"
            benefit_data["deductible_in_fam"] = benefit_data["deductible_in_ee"]

        # Build rx_display consolidated field
        rx_g = benefit_data.get("rx_generic", "")
        rx_p = benefit_data.get("rx_preferred_brand", "")
        rx_np = benefit_data.get("rx_non_preferred_brand", "")
        rx_parts = []
        if rx_g: rx_parts.append(f"Generic: {rx_g}")
        if rx_p: rx_parts.append(f"Preferred: {rx_p}")
        if rx_np: rx_parts.append(f"Non-Preferred: {rx_np}")
        benefit_data["rx_display"] = " / ".join(rx_parts)

        # Find matching plans in DB and update benefit fields
        from difflib import SequenceMatcher
        from src.plans.models import Plan, MedicalPlanDetails
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

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

        updated_count = 0
        async with AsyncSessionLocal() as db:
            # Find all plans for this carrier + year, fuzzy match on name
            stmt = (
                select(Plan)
                .options(selectinload(Plan.medical_details))
                .where(Plan.carrier == carrier, Plan.year == extracted_year)
            )
            result = await db.execute(stmt)
            candidates = result.scalars().all()

            incoming_name = plan_name.strip().lower()
            for candidate in candidates:
                candidate_name = candidate.plan_name.strip().lower()
                ratio = SequenceMatcher(None, candidate_name, incoming_name).ratio()
                if ratio >= 0.75:
                    log.info("Updating benefits for plan", plan_name=candidate.plan_name, ratio=round(ratio, 3))
                    if candidate.medical_details:
                        for field in BENEFIT_FIELDS:
                            if field in benefit_data and benefit_data[field]:
                                setattr(candidate.medical_details, field, benefit_data[field])
                        # Store rx_display in creditable_coverage field temporarily
                        # Actually store in the rx fields
                    else:
                        details = MedicalPlanDetails(plan_id=candidate.plan_id)
                        for field in BENEFIT_FIELDS:
                            if field in benefit_data and benefit_data[field]:
                                setattr(details, field, benefit_data[field])
                        db.add(details)
                    updated_count += 1

            await db.commit()

        results.append({
            "file": filename,
            "status": "success" if updated_count > 0 else "no_match",
            "carrier": carrier,
            "plan_name": plan_name,
            "year": extracted_year,
            "plans_updated": updated_count,
        })
        log.info("Benefit ingest complete", carrier=carrier, plan_name=plan_name, plans_updated=updated_count)

    return {
        "total_files": len(files),
        "files": results,
    }
