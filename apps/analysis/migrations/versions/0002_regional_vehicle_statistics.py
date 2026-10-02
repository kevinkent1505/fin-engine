"""regional vehicle statistics

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "regional_vehicle_statistics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("ingestion_run_id", sa.String(length=36), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(length=200), nullable=False),
        sa.Column("passenger_cars", sa.BigInteger(), nullable=False),
        sa.Column("buses", sa.BigInteger(), nullable=False),
        sa.Column("trucks", sa.BigInteger(), nullable=False),
        sa.Column("motorcycles", sa.BigInteger(), nullable=False),
        sa.Column("total", sa.BigInteger(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_key"],
            ["data_sources.source_key"],
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_runs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id",
            "year",
            "region",
            name="uq_regional_vehicle_statistics_run_year_region",
        ),
    )
    op.create_index(
        "ix_regional_vehicle_statistics_source_year_observed",
        "regional_vehicle_statistics",
        ["source_key", "year", "observed_at"],
        unique=False,
    )
    op.create_index(
        "ix_regional_vehicle_statistics_region_year",
        "regional_vehicle_statistics",
        ["region", "year"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_regional_vehicle_statistics_region_year",
        table_name="regional_vehicle_statistics",
    )
    op.drop_index(
        "ix_regional_vehicle_statistics_source_year_observed",
        table_name="regional_vehicle_statistics",
    )
    op.drop_table("regional_vehicle_statistics")
