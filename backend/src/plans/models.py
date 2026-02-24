import hashlib
from datetime import datetime, timezone

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from src.database import Base


class Plan(Base):
    __tablename__ = "plans"

    plan_id = Column(String, primary_key=True)
    plan_type = Column(String, nullable=False)  # "Medical", "Dental", "Vision"
    carrier = Column(String, nullable=False)
    plan_name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(String, nullable=False)

    ee_only = Column(Float, nullable=True)
    ee_spouse = Column(Float, nullable=True)
    ee_children = Column(Float, nullable=True)
    family = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    medical_details = relationship(
        "MedicalPlanDetails",
        back_populates="plan",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_plans_year_quarter", "year", "quarter"),)

    @staticmethod
    def generate_plan_id(carrier: str, plan_name: str, year: int, quarter: str) -> str:
        raw = f"{carrier.strip().lower()}|{plan_name.strip().lower()}|{year}|{quarter.strip().upper()}"
        return hashlib.sha256(raw.encode()).hexdigest()


class MedicalPlanDetails(Base):
    __tablename__ = "medical_plan_details"

    plan_id = Column(
        String,
        ForeignKey("plans.plan_id", ondelete="CASCADE"),
        primary_key=True,
    )

    in_network_deductible_type = Column(String, nullable=True)
    out_network_deductible_type = Column(String, nullable=True)
    in_network_oop_type = Column(String, nullable=True)
    out_network_oop_type = Column(String, nullable=True)

    wellness_benefit = Column(String, nullable=True)
    deductible_in_ee = Column(String, nullable=True)
    deductible_in_fam = Column(String, nullable=True)
    coinsurance_in = Column(String, nullable=True)
    oop_max_in_ee = Column(String, nullable=True)
    oop_max_in_fam = Column(String, nullable=True)

    pcp_copay = Column(String, nullable=True)
    specialist_copay = Column(String, nullable=True)
    inpatient_hospital = Column(String, nullable=True)
    outpatient_facility = Column(String, nullable=True)
    emergency_room = Column(String, nullable=True)
    urgent_care = Column(String, nullable=True)

    deductible_oon_ee = Column(String, nullable=True)
    deductible_oon_fam = Column(String, nullable=True)
    coinsurance_oon = Column(String, nullable=True)
    oop_max_oon_ee = Column(String, nullable=True)
    oop_max_oon_fam = Column(String, nullable=True)

    rx_generic = Column(String, nullable=True)
    rx_preferred_brand = Column(String, nullable=True)
    rx_non_preferred_brand = Column(String, nullable=True)

    hsa_qualified = Column(String, nullable=True)
    creditable_coverage = Column(String, nullable=True)
    dependent_coverage = Column(String, nullable=True)

    plan = relationship("Plan", back_populates="medical_details")
