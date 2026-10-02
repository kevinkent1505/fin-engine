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
from riil_analysis.models import VehicleValuationRequest
from riil_analysis.valuation import (
    database_listing_catalog_source,
    estimate_vehicle_value_from_database,
)


def _add_listing(
    session: Session,
    *,
    source_key: str,
    run_id: str,
    record_id: str,
    price: int,
    observed_at: datetime,
) -> None:
    session.add(
        VehicleRecord(
            id=record_id,
            source_key=source_key,
            source_record_id=record_id,
            source_url=f"https://example.invalid/{record_id}",
            make="Toyota",
            model="Avanza",
            variant="1.5 G CVT",
            type_name="Avanza 1.5 G CVT",
            year=2025,
            region="Jakarta",
            category="MARKETPLACE LISTING",
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            latest_metadata={},
        )
    )
    session.flush()
    session.add(
        VehicleObservation(
            id=f"obs-{record_id}",
            vehicle_record_id=record_id,
            ingestion_run_id=run_id,
            observed_at=observed_at,
            price=price,
            price_kind="listing",
            currency="IDR",
            njkb=None,
            weight_factor=None,
            dp_pkb=None,
            dp_pkb_expected=None,
            dp_pkb_difference=None,
            dp_pkb_check="not_available",
            metadata_json={},
        )
    )


def test_demo_only_database_is_labelled_and_used_as_demo(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'demo.sqlite'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    observed_at = datetime(2026, 10, 2, 1, 0, tzinfo=UTC)

    with Session(engine) as session:
        session.add(
            DataSource(
                source_key="marketplace_demo_seed",
                source_url="https://example.invalid/demo",
                created_at=observed_at,
            )
        )
        session.add(
            IngestionRun(
                id="demo-run",
                source_key="marketplace_demo_seed",
                started_at=observed_at,
                completed_at=observed_at,
                status="completed",
                authorization_reference=None,
                requested_limit=None,
                request_delay_seconds=2.0,
                quality={},
                audit={},
            )
        )
        session.flush()

        for index, price in enumerate((210_000_000, 220_000_000, 230_000_000), start=1):
            _add_listing(
                session,
                source_key="marketplace_demo_seed",
                run_id="demo-run",
                record_id=f"demo-{index}",
                price=price,
                observed_at=observed_at,
            )
        session.commit()

    assert database_listing_catalog_source(database_url) == "database_demo"

    result = estimate_vehicle_value_from_database(
        VehicleValuationRequest(
            make="Toyota",
            model="Avanza",
            year=2025,
            region="Jakarta",
        ),
        database_url,
    )

    assert result.valuation.estimate == 220_000_000
    assert result.sample_size == 3
    assert result.method == "comparable_market_demo_db_v1"
    engine.dispose()


def test_real_listings_take_precedence_over_demo_for_same_vehicle(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'mixed.sqlite'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    observed_at = datetime(2026, 10, 2, 1, 0, tzinfo=UTC)

    with Session(engine) as session:
        for source_key in ("marketplace_demo_seed", "marketplace_real_test"):
            session.add(
                DataSource(
                    source_key=source_key,
                    source_url=f"https://example.invalid/{source_key}",
                    created_at=observed_at,
                )
            )
            session.add(
                IngestionRun(
                    id=f"run-{source_key}",
                    source_key=source_key,
                    started_at=observed_at,
                    completed_at=observed_at,
                    status="completed",
                    authorization_reference=None,
                    requested_limit=None,
                    request_delay_seconds=2.0,
                    quality={},
                    audit={},
                )
            )
        session.flush()

        _add_listing(
            session,
            source_key="marketplace_demo_seed",
            run_id="run-marketplace_demo_seed",
            record_id="demo-1",
            price=220_000_000,
            observed_at=observed_at,
        )
        _add_listing(
            session,
            source_key="marketplace_real_test",
            run_id="run-marketplace_real_test",
            record_id="real-1",
            price=300_000_000,
            observed_at=observed_at,
        )
        _add_listing(
            session,
            source_key="marketplace_real_test",
            run_id="run-marketplace_real_test",
            record_id="real-2",
            price=320_000_000,
            observed_at=observed_at,
        )
        session.commit()

    assert database_listing_catalog_source(database_url) == "database"

    result = estimate_vehicle_value_from_database(
        VehicleValuationRequest(
            make="Toyota",
            model="Avanza",
            year=2025,
            region="Jakarta",
        ),
        database_url,
    )

    assert result.valuation.estimate == 310_000_000
    assert result.sample_size == 2
    assert result.method == "comparable_market_db_v1"
    engine.dispose()
