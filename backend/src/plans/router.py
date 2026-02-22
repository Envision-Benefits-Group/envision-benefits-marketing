import pandas as pd
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.database import get_db
from src.extraction.excel_generator import ExcelReportGenerator, BaseExcelGenerator
from src.extraction.comparison_generator import ComparisonExcelGenerator
from src.plans.models import Plan
from src.plans.repository import (
    browse_plans,
    get_plan_by_id,
    get_plans_by_ids,
    get_plans_by_quarter,
    update_plan,
)
from src.plans.schemas import ComparisonRequest, PlanResponse, PlanUpdate

router = APIRouter()

VALID_QUARTERS = {"Q1", "Q2", "Q3", "Q4"}


def _plan_to_row(plan: Plan) -> dict:
    """Convert a Plan DB record to a flat dict for DataFrame creation."""
    row = {
        "carrier": plan.carrier,
        "plan_name": plan.plan_name,
        "ee_only": plan.ee_only,
        "ee_spouse": plan.ee_spouse,
        "ee_children": plan.ee_children,
        "family": plan.family,
    }
    if plan.medical_details:
        d = plan.medical_details
        row.update({
            "in_network_deductible_type": d.in_network_deductible_type,
            "out_network_deductible_type": d.out_network_deductible_type,
            "in_network_oop_type": d.in_network_oop_type,
            "out_network_oop_type": d.out_network_oop_type,
            "wellness_benefit": d.wellness_benefit,
            "deductible_in_ee": d.deductible_in_ee,
            "deductible_in_fam": d.deductible_in_fam,
            "coinsurance_in": d.coinsurance_in,
            "oop_max_in_ee": d.oop_max_in_ee,
            "oop_max_in_fam": d.oop_max_in_fam,
            "pcp_copay": d.pcp_copay,
            "specialist_copay": d.specialist_copay,
            "inpatient_hospital": d.inpatient_hospital,
            "outpatient_facility": d.outpatient_facility,
            "emergency_room": d.emergency_room,
            "urgent_care": d.urgent_care,
            "deductible_oon_ee": d.deductible_oon_ee,
            "deductible_oon_fam": d.deductible_oon_fam,
            "coinsurance_oon": d.coinsurance_oon,
            "oop_max_oon_ee": d.oop_max_oon_ee,
            "oop_max_oon_fam": d.oop_max_oon_fam,
            "rx_generic": d.rx_generic,
            "rx_preferred_brand": d.rx_preferred_brand,
            "rx_non_preferred_brand": d.rx_non_preferred_brand,
            "hsa_qualified": d.hsa_qualified,
            "creditable_coverage": d.creditable_coverage,
            "dependent_coverage": d.dependent_coverage,
        })
    return row


@router.get("/browse", response_model=list[PlanResponse])
async def browse_all_plans(
    carrier: Optional[str] = Query(None, description="Filter by carrier name"),
    year: Optional[int] = Query(None, description="Filter by plan year"),
    quarter: Optional[str] = Query(None, description="Filter by quarter (Q1-Q4)"),
    network_type: Optional[str] = Query(None, description="Filter by network type (POS/PPO/HealthyNY)"),
    db: AsyncSession = Depends(get_db),
):
    """Browse all plans with optional filters."""
    if quarter and quarter.strip().upper() not in VALID_QUARTERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid quarter '{quarter}'. Must be one of: Q1, Q2, Q3, Q4",
        )

    plans = await browse_plans(db, carrier=carrier, year=year, quarter=quarter)

    # Network type is computed, so filter in Python
    if network_type:
        classifier = BaseExcelGenerator()
        filtered = []
        for plan in plans:
            row = {"carrier": plan.carrier, "plan_name": plan.plan_name}
            net = classifier._classify_network(row)
            if net == network_type:
                filtered.append(plan)
        plans = filtered

    return plans


@router.get("/medical", response_model=list[PlanResponse])
async def list_medical_plans(
    year: int = Query(..., description="Plan year"),
    quarter: str = Query(..., description="Quarter (Q1, Q2, Q3, Q4)"),
    db: AsyncSession = Depends(get_db),
):
    plans = await get_plans_by_quarter(db, year, quarter)
    return plans


@router.get("/master-template")
async def download_master_template(
    year: int = Query(..., description="Plan year"),
    quarter: str = Query(..., description="Quarter (Q1, Q2, Q3, Q4)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and download the Master Template Excel file
    containing all plans/carriers for the given year and quarter.
    """
    quarter = quarter.strip().upper()
    if quarter not in VALID_QUARTERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid quarter '{quarter}'. Must be one of: Q1, Q2, Q3, Q4",
        )

    stmt = (
        select(Plan)
        .options(selectinload(Plan.medical_details))
        .where(Plan.year == year, Plan.quarter == quarter)
        .order_by(Plan.carrier, Plan.plan_name)
    )
    result = await db.execute(stmt)
    plans = result.scalars().all()

    if not plans:
        raise HTTPException(
            status_code=404,
            detail=f"No plans found for {quarter} {year}.",
        )

    rows = [_plan_to_row(plan) for plan in plans]
    df = pd.DataFrame(rows)
    generator = ExcelReportGenerator()
    excel_file = generator.generate(df)

    filename = f"Master-Template-{quarter}-{year}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/comparison-template")
async def generate_comparison_template(
    body: ComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate the Marketing Renewal Comparison Excel.

    Produces:
      - <Carrier> Current_Renewal tab: enrolled plans with CURRENT | RENEWAL columns
      - <Carrier> Opts tabs: alternative plans with cross-sheet premium difference formulas
    """
    if not body.current_plan_ids and not body.renewal_plan_ids and not body.option_plan_ids:
        raise HTTPException(status_code=400, detail="No plan IDs provided.")

    current_plans = await get_plans_by_ids(db, body.current_plan_ids)
    renewal_plans = await get_plans_by_ids(db, body.renewal_plan_ids)
    option_plans  = await get_plans_by_ids(db, body.option_plan_ids)

    if not current_plans and not renewal_plans and not option_plans:
        raise HTTPException(status_code=404, detail="No plans found for the provided IDs.")

    current_df = pd.DataFrame([_plan_to_row(p) for p in current_plans]) if current_plans else pd.DataFrame()
    renewal_df = pd.DataFrame([_plan_to_row(p) for p in renewal_plans]) if renewal_plans else pd.DataFrame()
    options_df  = pd.DataFrame([_plan_to_row(p) for p in option_plans])  if option_plans  else pd.DataFrame()

    generator = ComparisonExcelGenerator()
    excel_file = generator.generate(current_df, renewal_df, options_df)

    filename = "Marketing-Renewal-Comparison.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.patch("/{plan_id}", response_model=PlanResponse)
async def patch_plan(
    plan_id: str,
    body: PlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    plan = await update_plan(db, plan_id, updates)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return plan
