from riil_analysis.normalization.vehicle import normalize_vehicle_observation
from riil_analysis.scrapers.registry import get_source_adapter
from riil_analysis.scrapers.sources.marketplace_demo_seed import (
    DEMO_LISTING_SOURCE,
    MarketplaceDemoSeedAdapter,
)


def test_demo_seed_generates_multiple_vehicle_choices() -> None:
    adapter = MarketplaceDemoSeedAdapter()
    records = adapter.run()

    assert len(records) >= 100
    assert {record.make_raw for record in records} >= {
        "Toyota",
        "Honda",
        "Mitsubishi",
        "Daihatsu",
    }
    assert len({(record.make_raw, record.model_raw) for record in records}) >= 6


def test_demo_seed_is_explicitly_synthetic() -> None:
    adapter = MarketplaceDemoSeedAdapter()
    raw = adapter.run()[0]

    assert raw.source == DEMO_LISTING_SOURCE
    assert raw.price_kind == "listing"
    assert raw.metadata["synthetic"] is True
    assert raw.metadata["not_real_marketplace_observation"] is True
    assert raw.metadata["access_basis"] == "synthetic_demo"

    normalized = normalize_vehicle_observation(raw)
    assert normalized.price > 0
    assert normalized.region == "Jakarta"


def test_demo_seed_is_registered() -> None:
    adapter = get_source_adapter(DEMO_LISTING_SOURCE)
    assert isinstance(adapter, MarketplaceDemoSeedAdapter)
