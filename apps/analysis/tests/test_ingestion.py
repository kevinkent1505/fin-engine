from datetime import UTC, datetime

from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.ingestion.pipeline import normalize_records
from riil_analysis.normalization.vehicle import normalize_price


def raw_record(
    *,
    record_id: str = "1",
    year: str = "2025",
    price: str | None = "214.000.000",
) -> RawVehicleObservation:
    return RawVehicleObservation(
        source="test",
        source_record_id=record_id,
        source_url="https://example.test/source",
        observed_at=datetime(2026, 10, 1, tzinfo=UTC),
        make_raw="TOYOTA",
        type_raw="AVANZA 1.5 VELOZ M/T",
        year_raw=year,
        region_raw="INDONESIA",
        price_raw=price,
        price_kind="njkb",
    )


def test_indonesian_price_format_is_normalized() -> None:
    assert normalize_price("6 .538.000.000") == 6_538_000_000


def test_pipeline_normalizes_and_deduplicates() -> None:
    records = [
        raw_record(),
        raw_record(),
        raw_record(record_id="2", price=None),
        raw_record(record_id="3", year="unknown"),
    ]

    output, report = normalize_records(records, source="test")

    assert len(output) == 1
    assert output[0].make == "Toyota"
    assert output[0].year == 2025
    assert output[0].price == 214_000_000
    assert output[0].region == "Indonesia"

    assert report.total_records == 4
    assert report.valid_records == 1
    assert report.duplicate_records == 1
    assert report.missing_price_records == 1
    assert report.invalid_year_records == 1
    assert report.invalid_records == 2
