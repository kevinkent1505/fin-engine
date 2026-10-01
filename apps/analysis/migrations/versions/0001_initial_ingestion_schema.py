"""initial ingestion persistence schema

Revision ID: 0001
Revises:
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("source_key"),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "authorization_reference",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column("requested_limit", sa.Integer(), nullable=True),
        sa.Column("request_delay_seconds", sa.Float(), nullable=True),
        sa.Column("quality", sa.JSON(), nullable=False),
        sa.Column("audit", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_key"],
            ["data_sources.source_key"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_runs_source_started",
        "ingestion_runs",
        ["source_key", "started_at"],
        unique=False,
    )

    op.create_table(
        "vehicle_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=150), nullable=True),
        sa.Column("variant", sa.String(length=255), nullable=True),
        sa.Column("type_name", sa.String(length=255), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=200), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_key"],
            ["data_sources.source_key"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_key",
            "source_record_id",
            name="uq_vehicle_records_source_record",
        ),
    )
    op.create_index(
        "ix_vehicle_records_vehicle_lookup",
        "vehicle_records",
        ["make", "model", "year", "region"],
        unique=False,
    )

    op.create_table(
        "vehicle_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_record_id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_run_id", sa.String(length=36), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column("price_kind", sa.String(length=40), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("njkb", sa.BigInteger(), nullable=True),
        sa.Column("weight_factor", sa.Float(), nullable=True),
        sa.Column("dp_pkb", sa.BigInteger(), nullable=True),
        sa.Column("dp_pkb_expected", sa.BigInteger(), nullable=True),
        sa.Column("dp_pkb_difference", sa.BigInteger(), nullable=True),
        sa.Column("dp_pkb_check", sa.String(length=30), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_runs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_record_id"],
            ["vehicle_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id",
            "vehicle_record_id",
            name="uq_vehicle_observations_run_record",
        ),
    )
    op.create_index(
        "ix_vehicle_observations_kind_observed",
        "vehicle_observations",
        ["price_kind", "observed_at"],
        unique=False,
    )
    op.create_index(
        "ix_vehicle_observations_record_observed",
        "vehicle_observations",
        ["vehicle_record_id", "observed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vehicle_observations_record_observed",
        table_name="vehicle_observations",
    )
    op.drop_index(
        "ix_vehicle_observations_kind_observed",
        table_name="vehicle_observations",
    )
    op.drop_table("vehicle_observations")

    op.drop_index(
        "ix_vehicle_records_vehicle_lookup",
        table_name="vehicle_records",
    )
    op.drop_table("vehicle_records")

    op.drop_index(
        "ix_ingestion_runs_source_started",
        table_name="ingestion_runs",
    )
    op.drop_table("ingestion_runs")
    op.drop_table("data_sources")
