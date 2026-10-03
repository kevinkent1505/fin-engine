from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from riil_analysis.database.models import (
    Base,
    DataSource,
    IngestionRun,
    VehicleObservation,
    VehicleRecord,
)
from riil_analysis.models import VehicleReferenceRequest
from riil_analysis.references import resolve_vehicle_references


def _seed_reference(
    session: Session,
    *,
    record_id: str,
    source_key: str,
    source_url: str,
    make: str,
    model: str,
    variant: str,
    year: int,
    price: int,
    price_kind: str,
) -> None:
    observed_at = datetime(2026, 10, 1, tzinfo=UTC)
    run_id = f"run-{record_id}"

    if session.get(DataSource, source_key) is None:
        session.add(
            DataSource(
                source_key=source_key,
                source_url=source_url,
                created_at=observed_at,
            )
        )

    session.add(
        IngestionRun(
            id=run_id,
            source_key=source_key,
            started_at=observed_at,
            completed_at=observed_at,
            status="completed",
            authorization_reference=None,
            requested_limit=None,
            request_delay_seconds=None,
            quality={},
            audit={},
        )
    )
    session.add(
        VehicleRecord(
            id=record_id,
            source_key=source_key,
            source_record_id=record_id,
            source_url=source_url,
            make=make,
            model=model,
            variant=variant,
            type_name=f"{model} {variant}",
            year=year,
            region="Indonesia",
            category="REFERENCE",
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            latest_metadata={},
        )
    )
    session.add(
        VehicleObservation(
            id=f"obs-{record_id}",
            vehicle_record_id=record_id,
            ingestion_run_id=run_id,
            observed_at=observed_at,
            price=price,
            price_kind=price_kind,
            currency="IDR",
            njkb=price if price_kind == "njkb" else None,
            weight_factor=None,
            dp_pkb=None,
            dp_pkb_expected=None,
            dp_pkb_difference=None,
            dp_pkb_check="not_applicable",
            metadata_json={},
        )
    )


def test_reference_resolution_returns_range_without_guessing_variant(tmp_path) -> None:
    database_path = tmp_path / "references.sqlite"
    database_url = f"sqlite+pysqlite:///{database_path}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_reference(
            session,
            record_id="njkb-a",
            source_key="kemendagri_njkb_2025",
            source_url="https://example.test/njkb",
            make="Toyota",
            model="Avanza",
            variant="1.3 E M/T",
            year=2025,
            price=168_000_000,
            price_kind="njkb",
        )
        _seed_reference(
            session,
            record_id="njkb-b",
            source_key="kemendagri_njkb_2025",
            source_url="https://example.test/njkb",
            make="Toyota",
            model="Avanza",
            variant="1.5 Veloz M/T",
            year=2025,
            price=214_000_000,
            price_kind="njkb",
        )
        session.commit()

    result = resolve_vehicle_references(
        VehicleReferenceRequest(make="Toyota", model="Avanza", year=2025),
        database_url,
    )

    assert result.njkb.status == "range"
    assert result.njkb.value is None
    assert result.njkb.low == 168_000_000
    assert result.njkb.high == 214_000_000
    assert result.njkb.candidate_count == 2
    assert result.auction_limit.status == "unavailable"

    engine.dispose()


def test_reference_resolution_returns_exact_when_unique_value(tmp_path) -> None:
    database_path = tmp_path / "references-exact.sqlite"
    database_url = f"sqlite+pysqlite:///{database_path}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_reference(
            session,
            record_id="auction-a",
            source_key="djp_vehicle_auction_limits",
            source_url="https://example.test/auction",
            make="Toyota",
            model="Kijang Innova",
            variant="G",
            year=2015,
            price=81_755_783,
            price_kind="auction_limit",
        )
        session.commit()

    result = resolve_vehicle_references(
        VehicleReferenceRequest(
            make="Toyota",
            model="Kijang Innova",
            year=2015,
        ),
        database_url,
    )

    assert result.auction_limit.status == "exact"
    assert result.auction_limit.value == 81_755_783
    assert result.auction_limit.low == 81_755_783
    assert result.auction_limit.high == 81_755_783
    assert result.njkb.status == "unavailable"

    engine.dispose()
