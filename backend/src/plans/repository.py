from difflib import SequenceMatcher
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.extraction.schemas import InsurancePlan
from src.plans.models import MedicalPlanDetails, Plan


MEDICAL_DETAIL_FIELDS = [
    "in_network_deductible_type", "out_network_deductible_type",
    "in_network_oop_type", "out_network_oop_type",
    "wellness_benefit",
    "deductible_in_ee", "deductible_in_fam",
    "coinsurance_in",
    "oop_max_in_ee", "oop_max_in_fam",
    "pcp_copay", "specialist_copay",
    "inpatient_hospital", "outpatient_facility",
    "emergency_room", "urgent_care",
    "deductible_oon_ee", "deductible_oon_fam",
    "coinsurance_oon",
    "oop_max_oon_ee", "oop_max_oon_fam",
    "rx_generic", "rx_preferred_brand", "rx_non_preferred_brand",
    "hsa_qualified", "creditable_coverage", "dependent_coverage",
]

PLAN_RATE_FIELDS = ["ee_only", "ee_spouse", "ee_children", "family"]

# Known carrier aliases for stripping from plan names before fuzzy comparison
CARRIER_ALIASES = [
    "independent health association", "independent health",
    "univera healthcare", "univera health", "univera",
    "excellus bluecross blueshield", "excellus bcbs", "excellus",
    "highmark blue cross blue shield", "highmark bcbs", "highmark",
    "iha",
]


def _normalize_plan_name(plan_name: str, carrier: str) -> str:
    """Strip carrier prefix from plan name for cleaner fuzzy comparison."""
    name = plan_name.strip().lower()
    carrier_lower = carrier.strip().lower()

    # Remove the carrier field value itself
    if name.startswith(carrier_lower):
        name = name[len(carrier_lower):].strip()

    # Remove known carrier aliases
    for alias in CARRIER_ALIASES:
        if name.startswith(alias):
            name = name[len(alias):].strip()

    return name


def _update_plan_fields(plan: Plan, data: InsurancePlan):
    plan.carrier = data.carrier
    plan.plan_name = data.plan_name
    plan.year = data.year
    plan.quarter = data.quarter.strip().upper()
    for field in PLAN_RATE_FIELDS:
        setattr(plan, field, getattr(data, field))


def _update_medical_details(details: MedicalPlanDetails, data: InsurancePlan):
    for field in MEDICAL_DETAIL_FIELDS:
        setattr(details, field, getattr(data, field))


async def _get_plan_with_details(session: AsyncSession, plan_id: str) -> Optional[Plan]:
    """Fetch a plan with medical_details eagerly loaded (avoids lazy loading greenlet errors)."""
    stmt = (
        select(Plan)
        .options(selectinload(Plan.medical_details))
        .where(Plan.plan_id == plan_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def save_plans(
    session: AsyncSession,
    plans: List[InsurancePlan],
) -> dict:
    inserted = 0
    updated_exact = 0
    updated_fuzzy = 0

    for plan_data in plans:
        quarter = plan_data.quarter.strip().upper()
        plan_id = Plan.generate_plan_id(
            plan_data.carrier, plan_data.plan_name, plan_data.year, quarter
        )

        # 1. Try exact hash match (eagerly load medical_details)
        existing = await _get_plan_with_details(session, plan_id)
        if existing:
            _update_plan_fields(existing, plan_data)
            if existing.medical_details:
                _update_medical_details(existing.medical_details, plan_data)
            else:
                details = MedicalPlanDetails(plan_id=plan_id)
                _update_medical_details(details, plan_data)
                session.add(details)
            updated_exact += 1
            continue

        # 2. Fuzzy fallback — search by carrier + quarter (eagerly load medical_details)
        stmt = (
            select(Plan)
            .options(selectinload(Plan.medical_details))
            .where(
                Plan.carrier == plan_data.carrier,
                Plan.quarter == quarter,
                Plan.year == plan_data.year,
                Plan.plan_type == "Medical",
            )
        )
        result = await session.execute(stmt)
        candidates = result.scalars().all()

        fuzzy_match = None
        best_ratio = 0.0
        incoming_name = _normalize_plan_name(plan_data.plan_name, plan_data.carrier)
        for candidate in candidates:
            candidate_name = _normalize_plan_name(candidate.plan_name, candidate.carrier)
            ratio = SequenceMatcher(None, candidate_name, incoming_name).ratio()
            if ratio >= 0.8 and ratio > best_ratio:
                best_ratio = ratio
                fuzzy_match = candidate

        if fuzzy_match:
            # Delete the old plan entirely (cascade deletes medical_details)
            await session.delete(fuzzy_match)
            await session.flush()

            # Insert fresh with the new plan_id
            new_plan = Plan(plan_id=plan_id, plan_type="Medical")
            _update_plan_fields(new_plan, plan_data)
            session.add(new_plan)

            new_details = MedicalPlanDetails(plan_id=plan_id)
            _update_medical_details(new_details, plan_data)
            session.add(new_details)
            updated_fuzzy += 1
            continue

        # 3. No match — insert new
        new_plan = Plan(
            plan_id=plan_id,
            plan_type="Medical",
        )
        _update_plan_fields(new_plan, plan_data)
        session.add(new_plan)

        new_details = MedicalPlanDetails(plan_id=plan_id)
        _update_medical_details(new_details, plan_data)
        session.add(new_details)
        inserted += 1

    await session.commit()
    return {
        "inserted": inserted,
        "updated_exact": updated_exact,
        "updated_fuzzy": updated_fuzzy,
    }


async def get_plans_by_quarter(
    session: AsyncSession, year: int, quarter: str
) -> List[Plan]:
    stmt = (
        select(Plan)
        .options(selectinload(Plan.medical_details))
        .where(Plan.year == year, Plan.quarter == quarter.strip().upper())
        .order_by(Plan.carrier, Plan.plan_name)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_plan_by_id(session: AsyncSession, plan_id: str) -> Optional[Plan]:
    return await _get_plan_with_details(session, plan_id)


async def update_plan(
    session: AsyncSession, plan_id: str, updates: dict
) -> Optional[Plan]:
    plan = await _get_plan_with_details(session, plan_id)
    if not plan:
        return None

    plan_fields = {"carrier", "plan_name", "ee_only", "ee_spouse", "ee_children", "family"}
    for key, value in updates.items():
        if key in plan_fields:
            setattr(plan, key, value)

    detail_updates = {k: v for k, v in updates.items() if k in MEDICAL_DETAIL_FIELDS}
    if detail_updates:
        if plan.medical_details:
            for key, value in detail_updates.items():
                setattr(plan.medical_details, key, value)
        else:
            details = MedicalPlanDetails(plan_id=plan_id, **detail_updates)
            session.add(details)

    await session.commit()
    await session.refresh(plan)
    return plan
