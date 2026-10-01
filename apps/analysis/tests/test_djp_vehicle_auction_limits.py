from datetime import UTC, datetime

from riil_analysis.normalization.vehicle import normalize_vehicle_observation
from riil_analysis.scrapers.sources.djp_vehicle_auction_limits import (
    DjpVehicleAuctionLimitsAdapter,
)


OBSERVED_AT = datetime(2026, 10, 1, tzinfo=UTC)


def test_discovers_only_vehicle_announcement_links() -> None:
    adapter = DjpVehicleAuctionLimitsAdapter()
    html = """
    <html><body>
      <a href="/id/pengumuman/lelang-mobil-daihatsu-luxio">
        Lelang 1 Unit Mobil Daihatsu Luxio 2017
      </a>
      <a href="/id/pengumuman/lelang-tanah-bogor">
        Lelang tanah di Bogor
      </a>
      <a href="https://example.com/id/pengumuman/lelang-mobil">
        Lelang Mobil eksternal
      </a>
    </body></html>
    """

    urls = adapter._discover_detail_urls(html)

    assert urls == [
        "https://www.pajak.go.id/id/pengumuman/lelang-mobil-daihatsu-luxio"
    ]


def test_parses_official_djp_vehicle_auction_limit() -> None:
    adapter = DjpVehicleAuctionLimitsAdapter()
    html = """
    <html>
      <head>
        <title>
          Lelang 1 Unit Mobil Daihatsu Luxio 2017 KPP Madya Jakarta Timur
          | Direktorat Jenderal Pajak
        </title>
      </head>
      <body>
        <h1>Lelang 1 Unit Mobil Daihatsu Luxio 2017 KPP Madya Jakarta Timur</h1>
        <p>Tanggal Lelang Rab, 25 Jun 2025</p>
        <p>Tempat Lelang Aula CBB - A &amp; B, Jakarta.</p>
        <p>
          Objek yang dilelang adalah satu unit mobil Daihatsu Luxio
          tahun pembuatan 2017. Kendaraan ditawarkan dengan
          nilai limit sebesar Rp89.600.000,- dan uang jaminan
          senilai Rp44.800.000.
        </p>
      </body>
    </html>
    """

    raw = adapter._parse_detail(
        html,
        source_url=(
            "https://www.pajak.go.id/id/pengumuman/"
            "lelang-1-unit-mobil-daihatsu-luxio-2017"
        ),
        observed_at=OBSERVED_AT,
    )

    assert raw is not None
    assert raw.make_raw == "Daihatsu"
    assert raw.type_raw == "Luxio"
    assert raw.year_raw == "2017"
    assert raw.price_raw == "89.600.000"
    assert raw.price_kind == "auction_limit"
    assert raw.metadata["deposit"] == 44_800_000

    normalized = normalize_vehicle_observation(raw)
    assert normalized.make == "Daihatsu"
    assert normalized.model == "Luxio"
    assert normalized.year == 2017
    assert normalized.price == 89_600_000
    assert normalized.price_kind == "auction_limit"
    assert normalized.njkb is None


def test_extracts_mileage_from_auction_announcement() -> None:
    adapter = DjpVehicleAuctionLimitsAdapter()
    html = """
    <html><body>
      <h1>
        Lelang 1 Unit Mobil Box Daihatsu Granmax 1298 CC
        Tahun Perakitan 2011 KPP Pratama Surabaya Rungkut
      </h1>
      <p>
        Odometer 186.767 km. Nilai Limit sebesar Rp48.000.000.
      </p>
    </body></html>
    """

    raw = adapter._parse_detail(
        html,
        source_url=(
            "https://www.pajak.go.id/id/pengumuman/"
            "lelang-mobil-box-daihatsu-granmax"
        ),
        observed_at=OBSERVED_AT,
    )

    assert raw is not None
    assert raw.make_raw == "Daihatsu"
    assert raw.type_raw == "Granmax 1298 CC"
    assert raw.metadata["mileage_km"] == 186_767


def test_page_without_auction_limit_is_not_ingested() -> None:
    adapter = DjpVehicleAuctionLimitsAdapter()
    html = """
    <html><body>
      <h1>Lelang Mobil Toyota Avanza Tahun 2018</h1>
      <p>Informasi kendaraan tanpa nilai limit.</p>
    </body></html>
    """

    raw = adapter._parse_detail(
        html,
        source_url=(
            "https://www.pajak.go.id/id/pengumuman/"
            "lelang-mobil-toyota-avanza"
        ),
        observed_at=OBSERVED_AT,
    )

    assert raw is None
