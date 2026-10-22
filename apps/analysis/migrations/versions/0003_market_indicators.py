"""Market indicator observations: independent, versioned non-vehicle data.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_indicator_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("ingestion_run_id", sa.String(length=36), nullable=False),
        sa.Column("indicator_code", sa.String(length=100), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(22, 6), nullable=False),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("original_publisher", sa.String(length=255), nullable=False),
        sa.Column("original_source_url", sa.Text(), nullable=False),
        sa.Column("origin_snapshot_url", sa.Text(), nullable=False),
        sa.Column("snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("revision_sha256", sa.String(length=64), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["source_key"], ["data_sources.source_key"]),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"]),
        sa.UniqueConstraint(
            "source_key", "indicator_code", "as_of", "revision_sha256",
            name="uq_market_indicator_source_date_revision",
        ),
    )
    op.create_index(
        "ix_market_indicator_code_date",
        "market_indicator_observations",
        ["indicator_code", "as_of"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_market_indicator_code_date",
        table_name="market_indicator_observations",
    )
    op.drop_table("market_indicator_observations")
