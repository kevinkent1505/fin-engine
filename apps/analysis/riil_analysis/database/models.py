from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DataSource(Base):
    __tablename__ = "data_sources"

    source_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_key: Mapped[str] = mapped_column(
        ForeignKey("data_sources.source_key"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    authorization_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    requested_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_delay_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    quality: Mapped[dict] = mapped_column(JSON, nullable=False)
    audit: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index("ix_ingestion_runs_source_started", "source_key", "started_at"),
    )


class VehicleRecord(Base):
    """
    Stable identity of one record in one source.

    For marketplace sources this is a listing identity. For NJKB and auction
    sources it is the source's stable record identifier. Fin Engine does not
    yet claim cross-source vehicle entity resolution.
    """

    __tablename__ = "vehicle_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_key: Mapped[str] = mapped_column(
        ForeignKey("data_sources.source_key"),
        nullable=False,
    )
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    variant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    region: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    latest_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "source_key",
            "source_record_id",
            name="uq_vehicle_records_source_record",
        ),
        Index(
            "ix_vehicle_records_vehicle_lookup",
            "make",
            "model",
            "year",
            "region",
        ),
    )


class VehicleObservation(Base):
    """Append-only observation of a source record at a point in time."""

    __tablename__ = "vehicle_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vehicle_record_id: Mapped[str] = mapped_column(
        ForeignKey("vehicle_records.id"),
        nullable=False,
    )
    ingestion_run_id: Mapped[str] = mapped_column(
        ForeignKey("ingestion_runs.id"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)

    njkb: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    weight_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    dp_pkb: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    dp_pkb_expected: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    dp_pkb_difference: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    dp_pkb_check: Mapped[str] = mapped_column(String(30), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ingestion_run_id",
            "vehicle_record_id",
            name="uq_vehicle_observations_run_record",
        ),
        Index(
            "ix_vehicle_observations_kind_observed",
            "price_kind",
            "observed_at",
        ),
        Index(
            "ix_vehicle_observations_record_observed",
            "vehicle_record_id",
            "observed_at",
        ),
    )
