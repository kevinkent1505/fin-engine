from datetime import UTC, datetime
import json

import pytest

from riil_analysis.normalization.vehicle import normalize_vehicle_observation
from riil_analysis.scrapers.polite_http import PoliteHttpClient
from riil_analysis.scrapers.sources.authorized_marketplace_crawl import (
    CarmudiAuthorizedCrawler,
    Mobil123AuthorizedCrawler,
    OlxAuthorizedCrawler,
)


OBSERVED_AT = datetime(2026, 10, 1, tzinfo=UTC)


DETAIL_HTML = """
<html>
<head>
  <title>2022 Toyota Avanza 1.3 E MPV - Example listing</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Vehicle",
    "name": "2022 Toyota Avanza 1.3 E MPV",
    "brand": {"@type": "Brand", "name": "Toyota"},
    "model": "Avanza",
    "vehicleModelDate": "2022",
    "vehicleTransmission": "Automatic",
    "fuelType": "Petrol",
    "mileageFromOdometer": {
      "@type": "QuantitativeValue",
      "value": 68000,
      "unitCode": "KMT"
    },
    "offers": {
      "@type": "Offer",
      "price": 178000000,
      "priceCurrency": "IDR"
    },
    "address": {
      "@type": "PostalAddress",
      "addressRegion": "DKI Jakarta"
    }
  }
  </script>
</head>
<body>
  <h1>2022 Toyota Avanza 1.3 E MPV</h1>
  <div>Rp 178.000.000</div>
  <div>DKI Jakarta</div>
</body>
</html>
"""


@pytest.mark.parametrize(
    ("adapter_type", "detail_url"),
    [
        (
            OlxAuthorizedCrawler,
            "https://www.olx.co.id/item/toyota-avanza-2022-iid-123456789",
        ),
        (
            Mobil123AuthorizedCrawler,
            "https://www.mobil123.com/dijual/toyota-avanza-dki-jakarta/19377388",
        ),
        (
            CarmudiAuthorizedCrawler,
            "https://www.carmudi.co.id/en/for-sale/toyota-avanza-dki-jakarta/19377388",
        ),
    ],
)
def test_jsonld_vehicle_detail_maps_to_listing(
    adapter_type,
    detail_url: str,
) -> None:
    adapter = adapter_type()
    adapter.set_authorization_reference("permission-001")

    raw = adapter._parse_detail(
        DETAIL_HTML,
        source_url=detail_url,
        observed_at=OBSERVED_AT,
    )

    assert raw is not None
    assert raw.price_kind == "listing"
    assert raw.make_raw == "Toyota"
    assert raw.model_raw == "Avanza"
    assert raw.year_raw == "2022"
    assert raw.region_raw == "DKI Jakarta"
    assert raw.price_raw == "178000000"
    assert raw.metadata["mileage"] == 68000
    assert raw.metadata["access_basis"] == "authorized_crawl"
    assert raw.metadata["authorization_reference"] == "permission-001"

    normalized = normalize_vehicle_observation(raw)
    assert normalized.make == "Toyota"
    assert normalized.model == "Avanza"
    assert normalized.year == 2022
    assert normalized.price == 178_000_000


def test_site_specific_detail_link_discovery() -> None:
    fixtures = [
        (
            OlxAuthorizedCrawler(),
            "https://www.olx.co.id/mobil-bekas_c198",
            "/item/toyota-avanza-iid-123456789",
        ),
        (
            Mobil123AuthorizedCrawler(),
            "https://www.mobil123.com/mobil-bekas-dijual",
            "/dijual/toyota-avanza-dki-jakarta/19377388",
        ),
        (
            CarmudiAuthorizedCrawler(),
            "https://www.carmudi.co.id/mobil-bekas-dijual/indonesia",
            "/en/for-sale/toyota-avanza-dki-jakarta/19377388",
        ),
    ]

    for adapter, base_url, href in fixtures:
        html = f'<html><body><a href="{href}">Vehicle</a></body></html>'
        urls = adapter._discover_detail_urls(html, base_url=base_url)
        assert len(urls) == 1
        assert urls[0].endswith(href)


def test_live_crawler_requires_authorization_reference() -> None:
    adapter = OlxAuthorizedCrawler()

    with pytest.raises(ValueError, match="--authorization-ref"):
        adapter.fetch()


def test_live_crawler_rejects_off_domain_start_url() -> None:
    adapter = CarmudiAuthorizedCrawler()
    adapter.set_authorization_reference("permission-001")
    adapter.set_start_url("https://example.com/cars")

    with pytest.raises(ValueError, match="authorized hosts"):
        adapter.fetch()


def test_rate_limit_has_one_second_floor() -> None:
    with pytest.raises(ValueError, match="at least 1.0"):
        PoliteHttpClient(delay_seconds=0.25)


def test_parse_bundle_does_not_require_network() -> None:
    adapter = Mobil123AuthorizedCrawler()
    adapter.set_authorization_reference("permission-001")
    payload = json.dumps(
        {
            "documents": [
                {
                    "url": (
                        "https://www.mobil123.com/dijual/"
                        "toyota-avanza-dki-jakarta/19377388"
                    ),
                    "html": DETAIL_HTML,
                }
            ]
        }
    ).encode("utf-8")

    records = adapter.parse(payload)
    assert len(records) == 1
    assert records[0].price_kind == "listing"
