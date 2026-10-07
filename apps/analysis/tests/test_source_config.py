from riil_analysis.config.sources import (
    OFFICIAL_SOURCES,
    latest_official_source,
    official_refresh_source_ids,
    official_source_aliases,
)


def test_official_source_ids_are_unique() -> None:
    source_ids = [source.source_id for source in OFFICIAL_SOURCES]
    assert len(source_ids) == len(set(source_ids))


def test_latest_aliases_resolve_to_highest_release_year() -> None:
    aliases = official_source_aliases()

    njkb = latest_official_source("njkb")
    vehicle_stock = latest_official_source("regional_vehicle_stock")

    assert aliases["njkb_latest"] == njkb.source_id
    assert aliases["vehicle_stock_latest"] == vehicle_stock.source_id

    assert njkb.release_year == max(
        source.release_year
        for source in OFFICIAL_SOURCES
        if source.family == "njkb"
    )
    assert vehicle_stock.release_year == max(
        source.release_year
        for source in OFFICIAL_SOURCES
        if source.family == "regional_vehicle_stock"
    )


def test_official_refresh_selects_one_latest_release_per_family() -> None:
    refresh_ids = official_refresh_source_ids()

    assert refresh_ids == (
        latest_official_source("njkb").source_id,
        latest_official_source("regional_vehicle_stock").source_id,
    )


def test_runtime_registry_accepts_semantic_latest_aliases() -> None:
    from riil_analysis.scrapers.registry import (
        get_regional_source_adapter,
        get_source_adapter,
        is_regional_source,
    )

    njkb_adapter = get_source_adapter("njkb_latest")
    bps_adapter = get_regional_source_adapter("vehicle_stock_latest")

    assert njkb_adapter.source_id == latest_official_source("njkb").source_id
    assert bps_adapter.source_id == latest_official_source(
        "regional_vehicle_stock"
    ).source_id
    assert is_regional_source("vehicle_stock_latest")
