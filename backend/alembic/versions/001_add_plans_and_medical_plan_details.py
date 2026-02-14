"""add plans and medical_plan_details tables

Revision ID: 001
Revises:
Create Date: 2026-02-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("plan_type", sa.String(), nullable=False),
        sa.Column("carrier", sa.String(), nullable=False),
        sa.Column("plan_name", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.String(), nullable=False),
        sa.Column("ee_only", sa.Float(), nullable=True),
        sa.Column("ee_spouse", sa.Float(), nullable=True),
        sa.Column("ee_children", sa.Float(), nullable=True),
        sa.Column("family", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("plan_id"),
    )
    op.create_index("ix_plans_year_quarter", "plans", ["year", "quarter"])

    op.create_table(
        "medical_plan_details",
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("in_network_deductible_type", sa.String(), nullable=True),
        sa.Column("out_network_deductible_type", sa.String(), nullable=True),
        sa.Column("in_network_oop_type", sa.String(), nullable=True),
        sa.Column("out_network_oop_type", sa.String(), nullable=True),
        sa.Column("wellness_benefit", sa.String(), nullable=True),
        sa.Column("deductible_in_ee", sa.String(), nullable=True),
        sa.Column("deductible_in_fam", sa.String(), nullable=True),
        sa.Column("coinsurance_in", sa.String(), nullable=True),
        sa.Column("oop_max_in_ee", sa.String(), nullable=True),
        sa.Column("oop_max_in_fam", sa.String(), nullable=True),
        sa.Column("pcp_copay", sa.String(), nullable=True),
        sa.Column("specialist_copay", sa.String(), nullable=True),
        sa.Column("inpatient_hospital", sa.String(), nullable=True),
        sa.Column("outpatient_facility", sa.String(), nullable=True),
        sa.Column("emergency_room", sa.String(), nullable=True),
        sa.Column("urgent_care", sa.String(), nullable=True),
        sa.Column("deductible_oon_ee", sa.String(), nullable=True),
        sa.Column("deductible_oon_fam", sa.String(), nullable=True),
        sa.Column("coinsurance_oon", sa.String(), nullable=True),
        sa.Column("oop_max_oon_ee", sa.String(), nullable=True),
        sa.Column("oop_max_oon_fam", sa.String(), nullable=True),
        sa.Column("rx_generic", sa.String(), nullable=True),
        sa.Column("rx_preferred_brand", sa.String(), nullable=True),
        sa.Column("rx_non_preferred_brand", sa.String(), nullable=True),
        sa.Column("hsa_qualified", sa.String(), nullable=True),
        sa.Column("creditable_coverage", sa.String(), nullable=True),
        sa.Column("dependent_coverage", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.plan_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("plan_id"),
    )


def downgrade() -> None:
    op.drop_table("medical_plan_details")
    op.drop_index("ix_plans_year_quarter", table_name="plans")
    op.drop_table("plans")
