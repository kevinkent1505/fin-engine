from datetime import UTC, datetime

from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.ingestion.pipeline import normalize_records
from riil_analysis.normalization.vehicle import (
    infer_model_variant,
    normalize_category,
    normalize_price,
    normalize_vehicle_observation,
)


def raw_record(
    *,
    record_id: str = "1",
    year: str = "2025",
    price: str | None = "214.000.000",
    weight: str | None = "1,050",
    dp_pkb: str | None = "224.700.000",
) -> RawVehicleObservation:
    return RawVehicleObservation(
        source="test",
        source_record_id=record_id,
        source_url="https://example.test/source",
        observed_at=datetime(2026, 10, 1, tzinfo=UTC),
        make_raw="TOYOTA",
        type_raw="AVANZA 1.5 VELOZ M/T (F654RM-GMSFJ)",
        year_raw=year,
        region_raw="INDONESIA",
        price_raw=price,
        price_kind="njkb",
        category_raw="MOBIL PENUMPANG- MINIBUS",
        metadata={
            "weight": weight,
            "dp_pkb": dp_pkb,
            "regulation": "Permendagri No. 7Tahun 2025",
        },
    )


def test_indonesian_price_format_is_normalized() -> None:
    assert normalize_price("6 .538.000.000") == 6_538_000_000


def test_category_spacing_is_normalized() -> None:
    assert (
        normalize_category("MOBIL PENUMPANG- SEDAN")
        == "MOBIL PENUMPANG - SEDAN"
    )


def test_reference_fields_are_typed_and_semantically_checked() -> None:
    result = normalize_vehicle_observation(raw_record())

    assert result.njkb == 214_000_000
    assert result.weight_factor == 1.05
    assert result.dp_pkb == 224_700_000
    assert result.dp_pkb_expected == 224_700_000
    assert result.dp_pkb_difference == 0
    assert result.dp_pkb_check == "pass"
    assert result.category == "MOBIL PENUMPANG - MINIBUS"
    assert result.metadata["regulation"] == "Permendagri No. 7 Tahun 2025"
    assert result.metadata["regulation_raw"] == "Permendagri No. 7Tahun 2025"


def test_semantic_mismatch_is_flagged_but_record_is_retained() -> None:
    result = normalize_vehicle_observation(
        raw_record(dp_pkb="200.000.000")
    )

    assert result.dp_pkb_check == "fail"
    assert result.dp_pkb_difference == 24_700_000


def test_model_variant_resolution_is_explicitly_heuristic() -> None:
    model, variant, method, confidence = infer_model_variant(
        None,
        None,
        "LAND CRUISER 300 VX-R A/T",
    )

    assert model == "Land Cruiser"
    assert variant == "300 VX-R A/T"
    assert method == "heuristic_type_prefix_v1"
    assert confidence == 0.75


def test_pipeline_normalizes_deduplicates_and_audits() -> None:
    records = [
        raw_record(),
        raw_record(),
        raw_record(record_id="2", price=None),
        raw_record(record_id="3", year="unknown"),
        raw_record(
            record_id="4",
            dp_pkb="200.000.000",
        ),
    ]

    output, report, audit = normalize_records(records, source="test")

    assert len(output) == 2
    assert output[0].make == "Toyota"
    assert output[0].model == "Avanza"
    assert output[0].variant == "1.5 VELOZ M/T"
    assert output[0].year == 2025
    assert output[0].price == 214_000_000
    assert output[0].region == "Indonesia"

    assert report.total_records == 5
    assert report.valid_records == 2
    assert report.duplicate_records == 1
    assert report.missing_price_records == 1
    assert report.invalid_year_records == 1
    assert report.invalid_records == 2

    assert report.semantic_checks_total == 2
    assert report.semantic_checks_passed == 1
    assert report.semantic_checks_failed == 1
    assert report.semantic_checks_skipped == 0

    assert audit.duplicate_record_ids == ["1"]
    assert len(audit.rejected_records) == 2
    assert audit.semantic_failure_record_ids == ["4"]
