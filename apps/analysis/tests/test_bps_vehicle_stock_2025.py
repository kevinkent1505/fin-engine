from datetime import UTC, datetime
import csv
import io

from bs4 import BeautifulSoup

from sqlalchemy import create_engine
import pytest

from riil_analysis.cli import ingest

from riil_analysis.database.models import Base
from riil_analysis.database.persistence import persist_regional_vehicle_statistics
from riil_analysis.regional import latest_regional_market_from_database
from riil_analysis.scrapers.sources.bps_vehicle_stock_2025 import (
    BpsVehicleStock2025Adapter,
)


def _table_html() -> bytes:
    rows = [
        ("Aceh", "223.567*", "3.021*", "81.937*", "2.590.309*", "2.898.834"),
        ("Sumatera Utara", "872.015*", "10.541*", "333.530*", "7.169.777*", "8.385.863"),
        ("Sumatera Barat", "386.835*", "4.959*", "134.595*", "2.584.223*", "3.110.612"),
        ("Riau", "472.776*", "6.225*", "256.187*", "4.288.370*", "5.023.558"),
        ("Jambi", "227.145*", "33.720*", "152.952*", "2.582.655*", "2.996.472"),
        ("Sumatera Selatan", "478.605*", "7.457*", "356.840*", "3.763.804*", "4.606.706"),
        ("DKI Jakarta", "2.336.960*", "37.981*", "527.841*", "9.376.276*", "12.279.058"),
        ("Jawa Barat", "2.980.773*", "36.679*", "779.518*", "24.260.590*", "28.057.560"),
        ("Jawa Tengah", "1.741.611*", "39.734*", "700.639*", "19.838.639*", "22.320.623"),
        ("Jawa Timur", "5.588.804*", "48.012*", "816.582*", "20.246.077*", "26.699.475"),
        ("Banten", "1.066.756*", "13.883*", "252.329*", "7.499.678*", "8.832.646"),
        ("Indonesia", "20.000.000", "200.000", "6.000.000", "120.000.000", "146.200.000"),
    ]
    body = "".join(
        "<tr><td>{index}</td><td>{region}</td><td>{cars}</td><td>{buses}</td>"
        "<td>{trucks}</td><td>{motorcycles}</td><td>{total}</td></tr>".format(
            index=index,
            region=region,
            cars=cars,
            buses=buses,
            trucks=trucks,
            motorcycles=motorcycles,
            total=total,
        )
        for index, (region, cars, buses, trucks, motorcycles, total) in enumerate(rows, start=1)
    )
    return f"<html><body><table>{body}</table></body></html>".encode()


def test_bps_parser_reads_official_table_shape() -> None:
    adapter = BpsVehicleStock2025Adapter()
    records = adapter.parse(_table_html())

    jakarta = next(record for record in records if record.region == "DKI Jakarta")
    assert jakarta.year == 2025
    assert jakarta.passenger_cars == 2_336_960
    assert jakarta.total == 12_279_058
    assert jakarta.metadata["reference_type"] == "official_regional_vehicle_stock"


def test_latest_regional_market_uses_latest_persisted_bps_snapshot(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'regional.sqlite'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    adapter = BpsVehicleStock2025Adapter()
    observations = adapter.parse(_table_html())
    observed_at = datetime(2026, 10, 2, 7, 0, tzinfo=UTC)
    observations = [
        observation.model_copy(update={"observed_at": observed_at})
        for observation in observations
    ]

    result = persist_regional_vehicle_statistics(
        database_url=database_url,
        source_key=adapter.source_id,
        source_url=adapter.source_url,
        observations=observations,
        started_at=observed_at,
        requested_limit=None,
    )
    assert result["inserted_statistics"] == len(observations)

    market = latest_regional_market_from_database(database_url)
    assert market.source == "bps_vehicle_stock_2025"
    assert market.year == 2025
    assert len(market.regions) == 7
    assert market.regions[0].region == "Jawa Timur"
    assert market.regions[0].passenger_cars == 5_588_804
    assert all(point.region != "Indonesia" for point in market.regions)


def test_bps_parser_rejects_non_numeric_missing_values() -> None:
    adapter = BpsVehicleStock2025Adapter()
    for missing_value in ("–", "...", "NA", "^1", "Data tidak tersedia"):
        with pytest.raises(ValueError, match="Invalid BPS vehicle count"):
            adapter._parse_count(missing_value)

    assert adapter._parse_count("223.567 *") == 223_567
    assert adapter._parse_count("2,590,309*") == 2_590_309
    assert adapter._parse_count("995") == 995


def test_bps_official_html_file_ingestion_without_database(tmp_path) -> None:
    html_file = tmp_path / "bps-2025.html"
    html_file.write_bytes(_table_html())
    output_file = tmp_path / "bps-preview.csv"

    result = ingest(
        source_id="vehicle_stock_latest",
        output_path=output_file,
        limit=None,
        input_file=html_file,
        authorization_ref=None,
        start_url=None,
        request_delay_seconds=2.0,
        persist_db=False,
    )

    assert result == 0
    content = output_file.read_text(encoding="utf-8")
    assert "DKI Jakarta" in content
    assert "bps_vehicle_stock_2025" in content
    assert "2336960" in content
    assert "manual_official_html_snapshot" in content


def test_bps_file_import_rejects_unsupported_formats(tmp_path) -> None:
    adapter = BpsVehicleStock2025Adapter()
    source = tmp_path / "bps-2025.json"
    source.write_text('{"region":"Aceh"}', encoding="utf-8")
    adapter.set_input_path(source)

    with pytest.raises(ValueError, match="accepts a saved official BPS HTML page"):
        adapter.fetch()


def _table_csv() -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["BPS Jumlah Kendaraan Bermotor Menurut Provinsi 2025"])
    writer.writerow([
        "No", "Provinsi", "Mobil Penumpang", "Bus",
        "Truk", "Sepeda Motor", "Jumlah Kendaraan Bermotor",
    ])
    soup = BeautifulSoup(_table_html(), "html.parser")
    for row in soup.find_all("tr"):
        writer.writerow([
            cell.get_text(" ", strip=True) for cell in row.find_all("td")
        ])
    return output.getvalue().encode("utf-8-sig")


def test_bps_official_csv_export_ingestion_and_provenance(tmp_path) -> None:
    source = tmp_path / "bps-2025.csv"
    source.write_bytes(_table_csv())
    adapter = BpsVehicleStock2025Adapter()
    adapter.set_input_path(source)
    records = adapter.run()

    jakarta = next(row for row in records if row.region == "DKI Jakarta")
    assert jakarta.passenger_cars == 2_336_960
    assert jakarta.total == 12_279_058
    assert jakarta.year == 2025
    assert jakarta.metadata["acquisition"] == "manual_official_csv_export"
    assert jakarta.metadata["import_filename"] == "bps-2025.csv"
    assert len(jakarta.metadata["import_sha256"]) == 64

    preview = tmp_path / "bps-preview.csv"
    assert ingest(
        source_id="vehicle_stock_latest",
        output_path=preview,
        limit=None,
        input_file=source,
        authorization_ref=None,
        start_url=None,
        request_delay_seconds=2.0,
        persist_db=False,
    ) == 0
    assert "DKI Jakarta" in preview.read_text(encoding="utf-8")


def test_bps_csv_rejects_incorrect_publication_year(tmp_path) -> None:
    source = tmp_path / "bps-2024.csv"
    source.write_bytes(_table_csv().replace(b"2025", b"2024"))
    adapter = BpsVehicleStock2025Adapter()
    adapter.set_input_path(source)
    with pytest.raises(ValueError, match="configured source year 2025"):
        adapter.run()


def test_bps_csv_rejects_mislabeled_table(tmp_path) -> None:
    source = tmp_path / "other-2025.csv"
    source.write_bytes(
        _table_csv().replace(b"Jumlah Kendaraan Bermotor", b"Other Indicators")
        .replace(b"Provinsi", b"Other Region")
    )
    adapter = BpsVehicleStock2025Adapter()
    adapter.set_input_path(source)
    with pytest.raises(ValueError, match="missing province and motor-vehicle"):
        adapter.run()


def test_bps_parser_excludes_rows_with_nonreconciling_totals() -> None:
    payload = _table_html().replace(
        b"<td>2.898.834</td>",
        b"<td>2.898.835</td>",
    )
    records = BpsVehicleStock2025Adapter().parse(payload)
    assert all(record.region != "Aceh" for record in records)
    assert len(records) == 11


def _complete_live_html() -> bytes:
    """Test fixture with all required regions and enough rows for a full page."""
    soup = BeautifulSoup(_table_html(), "html.parser")
    table = soup.find("table")
    assert table is not None
    original = table.find_all("tr")[0]
    for number in range(25):
        new_row = BeautifulSoup(str(original), "html.parser").find("tr")
        assert new_row is not None
        cells = new_row.find_all("td")
        cells[0].string = str(number + 100)
        cells[1].string = f"Test Province {number:02d}"
        table.append(new_row)
    heading = soup.new_tag("h1")
    heading.string = "Jumlah Kendaraan Bermotor Menurut Provinsi 2025"
    soup.body.insert(0, heading)
    return str(soup).encode("utf-8")


def test_bps_auto_refresh_uses_rendered_browser_after_incomplete_http(
    monkeypatch,
) -> None:
    adapter = BpsVehicleStock2025Adapter()
    monkeypatch.setattr(
        adapter, "fetch",
        lambda: b"<html><body><h1>BPS vehicle stock 2025</h1></body></html>",
    )

    def rendered():
        adapter._used_browser = True
        return _complete_live_html()

    monkeypatch.setattr(adapter, "fetch_rendered", rendered)

    records = adapter.run()
    assert len(records) >= 25
    assert any(item.region == "Jawa Timur" for item in records)
    assert all(
        item.metadata["acquisition"] == "public_statistics_table_browser"
        for item in records
    )


def test_bps_complete_http_response_does_not_open_browser(monkeypatch) -> None:
    adapter = BpsVehicleStock2025Adapter()
    monkeypatch.setattr(adapter, "fetch", _complete_live_html)

    def unexpected_browser():
        raise AssertionError("Complete HTTP results must not open a browser")

    monkeypatch.setattr(adapter, "fetch_rendered", unexpected_browser)
    records = adapter.run()
    assert len(records) >= 25
    assert all(
        item.metadata["acquisition"] == "public_statistics_table"
        for item in records
    )


def test_bps_refresh_rejects_incomplete_http_and_browser_snapshots(
    monkeypatch,
) -> None:
    adapter = BpsVehicleStock2025Adapter()
    monkeypatch.setattr(
        adapter,
        "fetch",
        lambda: b"<html><body><h1>2025</h1></body></html>",
    )
    monkeypatch.setattr(adapter, "fetch_rendered", _table_html)

    with pytest.raises(RuntimeError, match="No incomplete data were saved"):
        adapter.run()


def test_bps_file_import_never_attempts_browser_fallback(
    monkeypatch, tmp_path
) -> None:
    adapter = BpsVehicleStock2025Adapter()
    html_file = tmp_path / "official.html"
    html_file.write_bytes(_table_html())
    adapter.set_input_path(html_file)
    monkeypatch.setattr(
        adapter,
        "fetch_rendered",
        lambda: (_ for _ in ()).throw(AssertionError("Browser should not run")),
    )
    assert len(adapter.run()) == 12


def test_bps_rejects_live_table_with_incorrect_publication_year(
    monkeypatch,
) -> None:
    payload = _complete_live_html().replace(
        b"Provinsi 2025", b"Provinsi 2024"
    )
    adapter = BpsVehicleStock2025Adapter()
    monkeypatch.setattr(adapter, "fetch", lambda: payload)
    monkeypatch.setattr(adapter, "fetch_rendered", lambda: payload)
    with pytest.raises(RuntimeError, match="heading does not identify year"):
        adapter.run()

def test_official_csv_export_url_can_supply_complete_snapshot(monkeypatch) -> None:
    import httpx
    from riil_analysis.scrapers.sources import bps_vehicle_stock

    soup = BeautifulSoup(_complete_live_html(), "html.parser")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["BPS Jumlah Kendaraan Bermotor Menurut Provinsi 2025"])
    writer.writerow(["No", "Provinsi", "Mobil Penumpang", "Bus", "Truk",
                     "Sepeda Motor", "Jumlah Kendaraan Bermotor"])
    for tr in soup.find_all("tr"):
        writer.writerow([td.get_text(" ", strip=True) for td in tr.find_all("td")])
    csv_content = output.getvalue().encode("utf-8")
    monkeypatch.setenv(
        "BPS_VEHICLE_STOCK_CSV_URL",
        "https://www.bps.go.id/statistics-table/official-export.csv",
    )

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url):
            return httpx.Response(
                200, request=httpx.Request("GET", url), content=csv_content
            )

    monkeypatch.setattr(bps_vehicle_stock.httpx, "Client", FakeClient)
    rows = BpsVehicleStock2025Adapter().run()

    assert len(rows) >= 25
    assert any(row.region == "DKI Jakarta" for row in rows)
    assert rows[0].metadata["acquisition"] == "official_bps_csv_export_url"
    assert len(rows[0].metadata["import_sha256"]) == 64


def test_bps_403_fails_fast_without_browser_automation(monkeypatch) -> None:
    import httpx
    from riil_analysis.scrapers.sources import bps_vehicle_stock

    monkeypatch.delenv("BPS_VEHICLE_STOCK_CSV_URL", raising=False)
    adapter = BpsVehicleStock2025Adapter()

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url):
            return httpx.Response(
                403, request=httpx.Request("GET", url), content=b"blocked"
            )

    monkeypatch.setattr(bps_vehicle_stock.httpx, "Client", FakeClient)
    monkeypatch.setattr(
        adapter, "fetch_rendered",
        lambda: (_ for _ in ()).throw(AssertionError("Never retry 403 with browser")),
    )

    with pytest.raises(RuntimeError, match="BPS refused automated HTTP access"):
        adapter.run()
