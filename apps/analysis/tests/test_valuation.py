from datetime import UTC, datetime, timedelta
from pathlib import Path

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
    estimate_vehicle_value,
    estimate_vehicle_value_from_database,
    list_available_vehicles,
)


DATA_PATH = Path(__file__).parents[3] / "data" / "sample" / "vehicles.csv"


def test_vehicle_catalog_lists_distinct_supported_combinations() -> None:
    options = list_available_vehicles(str(DATA_PATH))

    assert any(
        option.make == "Toyota"
        and option.model == "Avanza"
        and option.year == 2023
        and option.region == "Jakarta"
        for option in options
    )
    assert any(
        option.make == "Honda"
        and option.model == "Brio"
        and option.year == 2023
        and option.region == "Jakarta"
        for option in options
    )
    assert len(
        [
            option
            for option in options
            if option.make == "Toyota"
            and option.model == "Avanza"
            and option.year == 2023
            and option.region == "Jakarta"
        ]
    ) == 1


def test_avanza_jakarta_baseline() -> None:
    result = estimate_vehicle_value(
        VehicleValuationRequest(
            make="Toyota",
            model="Avanza",
            year=2023,
            region="Jakarta",
        ),
        str(DATA_PATH),
    )

    assert result.valuation.estimate == 218_000_000
    assert result.valuation.low == 202_000_000
    assert result.valuation.high == 236_000_000
    assert result.sample_size == 13
    assert result.method == "comparable_market_v1"


def test_matching_is_case_insensitive() -> None:
    result = estimate_vehicle_value(
        VehicleValuationRequest(
            make="toyota",
            model="AVANZA",
            year=2023,
            region="jakarta",
        ),
        str(DATA_PATH),
    )

    assert result.sample_size == 13


def test_database_valuation_uses_latest_listing_per_record(tmp_path) -> None:
    database_path = tmp_path / "valuation.sqlite"
    database_url = f"sqlite+pysqlite:///{database_path}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    observed_at = datetime(2026, 10, 1, 1, 0, tzinfo=UTC)

    with Session(engine) as session:
        session.add(
            DataSource(
                source_key="marketplace_test",
                source_url="https://example.test",
                created_at=observed_at,
            )
        )
        session.add_all(
            [
                IngestionRun(
                    id="run-1",
                    source_key="marketplace_test",
                    started_at=observed_at,
                    completed_at=observed_at,
                    status="completed",
                    authorization_reference="test",
                    requested_limit=3,
                    request_delay_seconds=2.0,
                    quality={},
                    audit={},
                ),
                IngestionRun(
                    id="run-2",
                    source_key="marketplace_test",
                    started_at=observed_at + timedelta(days=1),
                    completed_at=observed_at + timedelta(days=1),
                    status="completed",
                    authorization_reference="test",
                    requested_limit=3,
                    request_delay_seconds=2.0,
                    quality={},
                    audit={},
                ),
            ]
        )

        for index in range(1, 4):
            session.add(
                VehicleRecord(
                    id=f"record-{index}",
                    source_key="marketplace_test",
                    source_record_id=f"listing-{index}",
                    source_url=f"https://example.test/{index}",
                    make="Toyota",
                    model="Avanza",
                    variant=None,
                    type_name="Avanza",
                    year=2025,
                    region="DKI Jakarta",
                    category="MARKETPLACE LISTING",
                    first_seen_at=observed_at,
                    last_seen_at=observed_at + timedelta(days=1),
                    latest_metadata={},
                )
            )

        session.flush()

        session.add_all(
            [
                VehicleObservation(
                    id="obs-old",
                    vehicle_record_id="record-1",
                    ingestion_run_id="run-1",
                    observed_at=observed_at,
                    price=250_000_000,
                    price_kind="listing",
                    currency="IDR",
                    njkb=None,
                    weight_factor=None,
                    dp_pkb=None,
                    dp_pkb_expected=None,
                    dp_pkb_difference=None,
                    dp_pkb_check="not_available",
                    metadata_json={},
                ),
                VehicleObservation(
                    id="obs-1",
                    vehicle_record_id="record-1",
                    ingestion_run_id="run-2",
                    observed_at=observed_at + timedelta(days=1),
                    price=210_000_000,
                    price_kind="listing",
                    currency="IDR",
                    njkb=None,
                    weight_factor=None,
                    dp_pkb=None,
                    dp_pkb_expected=None,
                    dp_pkb_difference=None,
                    dp_pkb_check="not_available",
                    metadata_json={},
                ),
                VehicleObservation(
                    id="obs-2",
                    vehicle_record_id="record-2",
                    ingestion_run_id="run-2",
                    observed_at=observed_at + timedelta(days=1),
                    price=220_000_000,
                    price_kind="listing",
                    currency="IDR",
                    njkb=None,
                    weight_factor=None,
                    dp_pkb=None,
                    dp_pkb_expected=None,
                    dp_pkb_difference=None,
                    dp_pkb_check="not_available",
                    metadata_json={},
                ),
                VehicleObservation(
                    id="obs-3",
                    vehicle_record_id="record-3",
                    ingestion_run_id="run-2",
                    observed_at=observed_at + timedelta(days=1),
                    price=230_000_000,
                    price_kind="listing",
                    currency="IDR",
                    njkb=None,
                    weight_factor=None,
                    dp_pkb=None,
                    dp_pkb_expected=None,
                    dp_pkb_difference=None,
                    dp_pkb_check="not_available",
                    metadata_json={},
                ),
            ]
        )
        session.commit()

    engine.dispose()

    result = estimate_vehicle_value_from_database(
        VehicleValuationRequest(
            make="toyota",
            model="AVANZA",
            year=2025,
            region="dki jakarta",
        ),
        database_url,
    )

    assert result.valuation.estimate == 220_000_000
    assert result.valuation.low == 210_000_000
    assert result.valuation.high == 230_000_000
    assert result.sample_size == 3
    assert result.method == "comparable_market_db_v1"
