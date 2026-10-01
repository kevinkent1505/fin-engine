from datetime import UTC, datetime

from riil_analysis.normalization.vehicle import normalize_vehicle_observation
from riil_analysis.scrapers.sources.kemendagri_njkb_2025 import (
    KemendagriNjkb2025Adapter,
)


def test_official_njkb_table_row_parses_into_raw_contract() -> None:
    adapter = KemendagriNjkb2025Adapter()

    # Representative row from the 2025 Permendagri NJKB appendix.
    row = [
        "473",
        "103255 94749",
        "TOYOTA",
        "AVANZA 1.5 VELOZ M/T (F654RM-GMSFJ)",
        "2025",
        "214.000.000",
        "1,050",
        "224.700.000",
    ]

    result = adapter._parse_table_row(
        row,
        category="MOBIL PENUMPANG - MINIBUS",
        observed_at=datetime(2026, 10, 1, tzinfo=UTC),
    )

    assert result is not None
    assert result.source == "kemendagri_njkb_2025"
    assert result.make_raw == "TOYOTA"
    assert result.type_raw.startswith("AVANZA")
    assert result.year_raw == "2025"
    assert result.price_raw == "214.000.000"
    assert result.price_kind == "njkb"
    assert result.metadata["coding"] == "103255 94749"


def test_representative_njkb_row_passes_semantic_validation() -> None:
    adapter = KemendagriNjkb2025Adapter()
    raw = adapter._parse_table_row(
        [
            "473",
            "103255 94749",
            "TOYOTA",
            "AVANZA 1.5 VELOZ M/T (F654RM-GMSFJ)",
            "2025",
            "214.000.000",
            "1,050",
            "224.700.000",
        ],
        category="MOBIL PENUMPANG- MINIBUS",
        observed_at=datetime(2026, 10, 1, tzinfo=UTC),
    )

    assert raw is not None
    result = normalize_vehicle_observation(raw)

    assert result.model == "Avanza"
    assert result.variant == "1.5 VELOZ M/T"
    assert result.njkb == 214_000_000
    assert result.weight_factor == 1.05
    assert result.dp_pkb == 224_700_000
    assert result.dp_pkb_check == "pass"


def test_table_header_is_ignored() -> None:
    adapter = KemendagriNjkb2025Adapter()

    result = adapter._parse_table_row(
        [
            "NO",
            "KODING",
            "MEREK",
            "TYPE",
            "TH BUAT",
            "NJKB",
            "BOBOT",
            "DP PKB",
        ],
        category="MOBIL PENUMPANG - SEDAN",
        observed_at=datetime(2026, 10, 1, tzinfo=UTC),
    )

    assert result is None
