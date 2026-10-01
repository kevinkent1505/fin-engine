from datetime import UTC
import pytest

from riil_analysis.normalization.vehicle import normalize_vehicle_observation
from riil_analysis.scrapers.sources.authorized_marketplace_csv import (
    CarmudiAuthorizedFeedAdapter,
    Mobil123AuthorizedFeedAdapter,
    OlxAuthorizedFeedAdapter,
)


FEED = b"""listing_id,listing_url,make,model,variant,year,price,region,mileage_km,transmission,fuel,seller_type,observed_at,currency
abc-123,https://partner.example/listing/abc-123,TOYOTA,Avanza,1.5 G CVT,2023,218000000,Jakarta,24500,CVT,Petrol,Dealer,2026-10-01T07:00:00Z,IDR
"""


@pytest.mark.parametrize(
    ("adapter_type", "source_id"),
    [
        (OlxAuthorizedFeedAdapter, "olx_authorized_feed"),
        (Mobil123AuthorizedFeedAdapter, "mobil123_authorized_feed"),
        (CarmudiAuthorizedFeedAdapter, "carmudi_authorized_feed"),
    ],
)
def test_authorized_marketplace_feed_maps_to_listing_contract(
    adapter_type,
    source_id: str,
) -> None:
    adapter = adapter_type()
    adapter.set_authorization_reference("partner-contract-001")

    records = adapter.parse(FEED)

    assert len(records) == 1
    raw = records[0]
    assert raw.source == source_id
    assert raw.price_kind == "listing"
    assert raw.make_raw == "TOYOTA"
    assert raw.model_raw == "Avanza"
    assert raw.variant_raw == "1.5 G CVT"
    assert raw.metadata["mileage_km"] == 24_500
    assert raw.metadata["access_basis"] == "authorized_feed"
    assert raw.metadata["authorization_reference"] == "partner-contract-001"
    assert raw.observed_at.tzinfo == UTC

    normalized = normalize_vehicle_observation(raw)
    assert normalized.make == "Toyota"
    assert normalized.model == "Avanza"
    assert normalized.variant == "1.5 G CVT"
    assert normalized.year == 2023
    assert normalized.price == 218_000_000
    assert normalized.price_kind == "listing"


def test_authorized_feed_fetch_requires_local_file() -> None:
    adapter = OlxAuthorizedFeedAdapter()
    adapter.set_authorization_reference("partner-contract-001")

    with pytest.raises(ValueError, match="--input-file"):
        adapter.fetch()


def test_authorized_feed_fetch_requires_authorization_reference(
    tmp_path,
) -> None:
    feed = tmp_path / "feed.csv"
    feed.write_bytes(FEED)

    adapter = Mobil123AuthorizedFeedAdapter()
    adapter.set_input_path(feed)

    with pytest.raises(ValueError, match="--authorization-ref"):
        adapter.fetch()


def test_authorized_feed_requires_expected_columns() -> None:
    adapter = CarmudiAuthorizedFeedAdapter()
    adapter.set_authorization_reference("partner-contract-001")

    with pytest.raises(ValueError, match="missing required columns"):
        adapter.parse(b"listing_id,make\n1,Toyota\n")
