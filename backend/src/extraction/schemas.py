from pydantic import BaseModel, Field
from typing import Optional, List

# Copied from your src/Misc/extraction.py
class InsurancePlan(BaseModel):
    carrier: str = Field(description="Carrier")
    plan_name: str = Field(description="Full plan name")

    in_network_deductible_type: str = Field(description="T for True Family or E for Embedded")
    out_network_deductible_type: str = Field(description="T for True Family or E for Embedded")

    ee_only: Optional[float] = Field(None, description="Employee Only / Single rate")
    ee_spouse: Optional[float] = Field(None, description="Employee + Spouse rate")
    ee_children: Optional[float] = Field(None, description="Employee + Child(ren) rate")
    family: Optional[float] = Field(None, description="Family rate")

    wellness_benefit: str = Field(description="Wellness Benefit description")
    deductible_in_ee: str = Field(description="In-network Deductible Individual (Use 'None' for N/A)")
    deductible_in_fam: str = Field(description="In-network Deductible Family (Use 'None' for N/A)")
    coinsurance_in: str = Field(description="In-network Coinsurance (Remove 'FS', use 'None' for 0% or N/A)")
    oop_max_in_ee: str = Field(description="In-network OOP Max Individual")
    oop_max_in_fam: str = Field(description="In-network OOP Max Family")

    pcp_copay: str = Field(description="PCP Visit cost")
    specialist_copay: str = Field(description="Specialist Visit cost")
    inpatient_hospital: str = Field(description="Inpatient Hospital cost")
    outpatient_facility: str = Field(description="Outpatient Facility cost")
    emergency_room: str = Field(description="ER Services cost")
    urgent_care: str = Field(description="Urgent Care cost")

    deductible_oon_ee: str = Field(description="OON Deductible Individual")
    deductible_oon_fam: str = Field(description="OON Deductible Family")
    coinsurance_oon: str = Field(description="OON Coinsurance (Remove 'FS')")
    rx_generic: str = Field(description="Generic drug cost (Standardize format)")
    rx_preferred_brand: str = Field(description="Preferred Brand cost (Standardize format)")
    rx_non_preferred_brand: str = Field(description="Non-Preferred cost (Standardize format)")

    hsa_qualified: str = Field(description="Yes or No")
    creditable_coverage: str = Field(description="Yes or No")
    dependent_coverage: str = Field(description="Standardized to 'Age 26'")

class PlanList(BaseModel):
    plans: List[InsurancePlan]