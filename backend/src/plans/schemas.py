from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MedicalDetailsResponse(BaseModel):
    in_network_deductible_type: Optional[str] = None
    out_network_deductible_type: Optional[str] = None
    in_network_oop_type: Optional[str] = None
    out_network_oop_type: Optional[str] = None
    wellness_benefit: Optional[str] = None
    deductible_in_ee: Optional[str] = None
    deductible_in_fam: Optional[str] = None
    coinsurance_in: Optional[str] = None
    oop_max_in_ee: Optional[str] = None
    oop_max_in_fam: Optional[str] = None
    pcp_copay: Optional[str] = None
    specialist_copay: Optional[str] = None
    inpatient_hospital: Optional[str] = None
    outpatient_facility: Optional[str] = None
    emergency_room: Optional[str] = None
    urgent_care: Optional[str] = None
    deductible_oon_ee: Optional[str] = None
    deductible_oon_fam: Optional[str] = None
    coinsurance_oon: Optional[str] = None
    oop_max_oon_ee: Optional[str] = None
    oop_max_oon_fam: Optional[str] = None
    rx_generic: Optional[str] = None
    rx_preferred_brand: Optional[str] = None
    rx_non_preferred_brand: Optional[str] = None
    hsa_qualified: Optional[str] = None
    creditable_coverage: Optional[str] = None
    dependent_coverage: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    plan_id: str
    plan_type: str
    carrier: str
    plan_name: str
    year: int
    quarter: str
    ee_only: Optional[float] = None
    ee_spouse: Optional[float] = None
    ee_children: Optional[float] = None
    family: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    medical_details: Optional[MedicalDetailsResponse] = None

    model_config = {"from_attributes": True}


class ComparisonRequest(BaseModel):
    current_plan_ids: list[str] = []   # enrolled plans — old (current year) pricing
    renewal_plan_ids: list[str] = []   # renewal pricing for the same plans, matched by position
    option_plan_ids: list[str] = []    # alternative plans shown in <Carrier> Opts tabs


class PlanUpdate(BaseModel):
    carrier: Optional[str] = None
    plan_name: Optional[str] = None
    ee_only: Optional[float] = None
    ee_spouse: Optional[float] = None
    ee_children: Optional[float] = None
    family: Optional[float] = None
    in_network_deductible_type: Optional[str] = None
    out_network_deductible_type: Optional[str] = None
    in_network_oop_type: Optional[str] = None
    out_network_oop_type: Optional[str] = None
    wellness_benefit: Optional[str] = None
    deductible_in_ee: Optional[str] = None
    deductible_in_fam: Optional[str] = None
    coinsurance_in: Optional[str] = None
    oop_max_in_ee: Optional[str] = None
    oop_max_in_fam: Optional[str] = None
    pcp_copay: Optional[str] = None
    specialist_copay: Optional[str] = None
    inpatient_hospital: Optional[str] = None
    outpatient_facility: Optional[str] = None
    emergency_room: Optional[str] = None
    urgent_care: Optional[str] = None
    deductible_oon_ee: Optional[str] = None
    deductible_oon_fam: Optional[str] = None
    coinsurance_oon: Optional[str] = None
    oop_max_oon_ee: Optional[str] = None
    oop_max_oon_fam: Optional[str] = None
    rx_generic: Optional[str] = None
    rx_preferred_brand: Optional[str] = None
    rx_non_preferred_brand: Optional[str] = None
    hsa_qualified: Optional[str] = None
    creditable_coverage: Optional[str] = None
    dependent_coverage: Optional[str] = None
