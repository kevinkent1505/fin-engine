from datetime import UTC, datetime

from sqlalchemy import create_engine

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
