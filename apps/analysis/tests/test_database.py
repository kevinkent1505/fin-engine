from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from riil_analysis.database.config import normalize_database_url
from riil_analysis.database.models import (
    Base,
    DataSource,
    IngestionRun,
    VehicleObservation,
    VehicleRecord,
)
from riil_analysis.database.persistence import persist_ingestion
from riil_analysis.database.timestamps import as_utc
from riil_analysis.ingestion.models import (
    CanonicalVehicleObservation,
    IngestionAudit,
    IngestionQualityReport,
)


def observation(
    *,
    price: int,
    observed_at: datetime,
) -> CanonicalVehicleObservation:
    return CanonicalVehicleObservation(
        source="olx_authorized_crawl",
        source_record_id="listing-123",
        source_url="https://www.olx.co.id/item/example-iid-123456789",
        observed_at=observed_at,
        make="Toyota",
        model="Avanza",
        variant="1.5 G CVT",
        type_name="Avanza 1.5 G CVT",
        year=2023,
        region="DKI Jakarta",
        price=price,
        price_kind="listing",
        currency="IDR",
        category="MARKETPLACE LISTING",
        metadata={
            "access_basis": "authorized_crawl",
            "authorization_reference": "permission-001",
        },
    )


def quality() -> IngestionQualityReport:
    return IngestionQualityReport(
        source="olx_authorized_crawl",
        total_records=1,
        valid_records=1,
    )


def test_neon_style_url_uses_psycopg3() -> None:
    assert normalize_database_url(
        "postgresql://u:p@example.neon.tech/db?sslmode=require"
    ).startswith("postgresql+psycopg://")

    assert normalize_database_url(
        "postgres://u:p@example.neon.tech/db?sslmode=require"
    ).startswith("postgresql+psycopg://")


def test_persistence_keeps_identity_and_appends_observations(tmp_path) -> None:
    database_path = tmp_path / "fin-engine.sqlite"
    database_url = f"sqlite+pysqlite:///{database_path}"

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    first_time = datetime(2026, 10, 1, 1, 0, tzinfo=UTC)
    second_time = datetime(2026, 10, 2, 1, 0, tzinfo=UTC)

    first = persist_ingestion(
        database_url=database_url,
        source_key="olx_authorized_crawl",
        source_url="https://www.olx.co.id/",
        observations=[observation(price=218_000_000, observed_at=first_time)],
        report=quality(),
        audit=IngestionAudit(),
        started_at=first_time,
        authorization_reference="permission-001",
        requested_limit=5,
        request_delay_seconds=2.0,
    )
    second = persist_ingestion(
        database_url=database_url,
        source_key="olx_authorized_crawl",
        source_url="https://www.olx.co.id/",
        observations=[observation(price=214_000_000, observed_at=second_time)],
        report=quality(),
        audit=IngestionAudit(),
        started_at=second_time,
        authorization_reference="permission-001",
        requested_limit=5,
        request_delay_seconds=2.0,
    )

    assert first["created_records"] == 1
    assert first["inserted_observations"] == 1
    assert second["created_records"] == 0
    assert second["updated_records"] == 1
    assert second["inserted_observations"] == 1

    engine = create_engine(database_url)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(DataSource)) == 1
        assert session.scalar(select(func.count()).select_from(IngestionRun)) == 2
        assert session.scalar(select(func.count()).select_from(VehicleRecord)) == 1
        assert (
            session.scalar(select(func.count()).select_from(VehicleObservation))
            == 2
        )

        record = session.scalar(select(VehicleRecord))
        assert record is not None
        assert record.first_seen_at.date() == first_time.date()
        assert record.last_seen_at.date() == second_time.date()

        prices = session.scalars(
            select(VehicleObservation.price).order_by(
                VehicleObservation.observed_at
            )
        ).all()
        assert prices == [218_000_000, 214_000_000]

    engine.dispose()


def test_database_naive_timestamps_are_interpreted_as_utc() -> None:
    raw_from_sqlite = datetime(2026, 10, 2, 1, 0)
    same_in_utc_plus_eight = datetime(
        2026, 10, 2, 9, 0, tzinfo=timezone(timedelta(hours=8))
    )

    assert as_utc(raw_from_sqlite) == datetime(2026, 10, 2, 1, 0, tzinfo=UTC)
    assert as_utc(same_in_utc_plus_eight) == as_utc(raw_from_sqlite)


def test_sqlite_persistence_normalizes_timezones_and_older_observations(
    tmp_path,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'timestamps.sqlite'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    first_time = datetime(
        2026, 10, 2, 9, 0, tzinfo=timezone(timedelta(hours=8))
    )
    older_time = datetime(2026, 10, 1, 23, 30, tzinfo=UTC)

    for price, observed_at in [
        (218_000_000, first_time),
        (214_000_000, older_time),
    ]:
        persist_ingestion(
            database_url=database_url,
            source_key="olx_authorized_crawl",
            source_url="https://www.olx.co.id/",
            observations=[observation(price=price, observed_at=observed_at)],
            report=quality(),
            audit=IngestionAudit(),
            started_at=observed_at,
            authorization_reference="permission-001",
            requested_limit=5,
            request_delay_seconds=2.0,
        )

    engine = create_engine(database_url)
    with Session(engine) as session:
        record = session.scalar(select(VehicleRecord))
        assert record is not None
        # SQLite strips tzinfo. We store UTC wall time explicitly.
        assert record.first_seen_at == datetime(2026, 10, 2, 1, 0)
        assert record.last_seen_at == datetime(2026, 10, 2, 1, 0)

        timestamps = session.scalars(
            select(VehicleObservation.observed_at).order_by(
                VehicleObservation.observed_at
            )
        ).all()
        assert timestamps == [
            datetime(2026, 10, 1, 23, 30),
            datetime(2026, 10, 2, 1, 0),
        ]
        assert session.scalar(
            select(func.count()).select_from(VehicleObservation)
        ) == 2

    engine.dispose()
