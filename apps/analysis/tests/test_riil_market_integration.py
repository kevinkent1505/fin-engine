"""Riil first-phase feed: no network, no private user data in test fixtures."""
from datetime import date
import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from riil_analysis.cli import import_riil_market
from riil_analysis.database.models import (
    Base, DataSource, IngestionRun, MarketIndicatorObservation,
)
from riil_analysis.integrations.riil_market import (
    SOURCE_KEY, parse_riil_market_snapshot,
)
from riil_analysis.integrations.riil_market_persistence import (
    persist_riil_market_snapshot,
)


def _fixture(*, ihsg_value=5185.11) -> bytes:
    def item(value, unit=None, *, as_of="2026-09-30"):
        return {
            "value": value,
            **({"unit": unit} if unit else {}),
            "as_of": as_of,
            "source_name": "Original Publisher",
            "source_url": "https://source.example/data",
        }

    doc = {
        "updated_at": "2026-10-17",
        "indicators": {
            "usd_idr": item(18052, "IDR per USD", as_of="2026-10-16"),
            "inflation_yoy": item(3.28, "percent, year on year"),
            "oil_icp": item(112.81, "USD per barrel"),
            "ihsg": {
                **item(ihsg_value, as_of="2026-10-16"),
                "previous": 6093.76,
                "previous_as_of": "2026-10-09",
                "previous_source_name": "Historical Publisher",
                "previous_source_url": "https://source.example/previous",
            },
            "gold_antam": {
                **item(None, "IDR per gram", as_of="2026-10-16"),
                "price": 2600000,
                "buyback": 2337000,
            },
            "fuel": {
                **item(None, "IDR per litre", as_of="2026-10-01"),
                "prices": {
                    "pertalite": 10000,
                    "pertamax": 15950,
                    "pertamax_green": 19150,
                    "pertamax_turbo": 19600,
                    "dexlite": 23700,
                    "pertamina_dex": 25200,
                },
            },
        },
        "account": {
            "email": "should-not-appear@example.test",
            "salary": 999999,
        },
    }
    return json.dumps(doc).encode("utf-8")


def test_market_snapshot_import_maps_only_approved_curated_fields() -> None:
    snapshot = parse_riil_market_snapshot(_fixture())
    assert len(snapshot.observations) == 13
    assert snapshot.updated_at == date(2026, 10, 17)
    data = {row.code: row for row in snapshot.observations}
    assert data["usd_idr"].value == 18052
    assert data["gold_antam_buyback"].value == 2337000
    assert data["ihsg_previous"].as_of == date(2026, 10, 9)
    assert data["ihsg_previous"].original_publisher == "Historical Publisher"
    assert set(data["usd_idr"].metadata) == {
        "origin_product", "origin_type", "riil_updated_at", "verification",
    }
    assert "should-not-appear" not in repr(snapshot)
    assert "salary" not in repr(snapshot)
    assert all(row.metadata["verification"] ==
               "not_independently_verified_by_fin_engine"
               for row in snapshot.observations)


def test_market_snapshot_idempotency_and_append_only_revision(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'indicators.sqlite'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    first = parse_riil_market_snapshot(_fixture())
    result1 = persist_riil_market_snapshot(database_url=database_url, snapshot=first)
    assert result1["inserted_observations"] == 13
    assert result1["skipped_existing"] == 0
    assert result1["run_id"] is not None

    result2 = persist_riil_market_snapshot(database_url=database_url, snapshot=first)
    assert result2["inserted_observations"] == 0
    assert result2["skipped_existing"] == 13
    assert result2["run_id"] is None

    correction = parse_riil_market_snapshot(_fixture(ihsg_value=5186.25))
    result3 = persist_riil_market_snapshot(
        database_url=database_url, snapshot=correction,
    )
    assert result3["inserted_observations"] == 1
    assert result3["skipped_existing"] == 12

    engine = create_engine(database_url)
    with Session(engine) as session:
        observations = session.scalars(select(MarketIndicatorObservation)).all()
        runs = session.scalars(select(IngestionRun)).all()
        sources = session.scalars(select(DataSource)).all()
        assert len(observations) == 14
        assert len(runs) == 2
        assert len(sources) == 1
        assert sources[0].source_key == SOURCE_KEY
        revisions = [r for r in observations if r.indicator_code == "ihsg"]
        assert len(revisions) == 2
        assert {str(r.value) for r in revisions} == {
            "5185.110000", "5186.250000",
        }
        assert all("salary" not in str(row.metadata_json) for row in observations)
        assert runs[1].audit["independently_verified"] is False
    engine.dispose()


@pytest.mark.parametrize("key", ["fuel", "usd_idr", "gold_antam"])
def test_market_snapshot_missing_required_indicators_fails(key) -> None:
    doc = json.loads(_fixture())
    del doc["indicators"][key]
    with pytest.raises(ValueError, match="incomplete"):
        parse_riil_market_snapshot(json.dumps(doc).encode())


def test_market_snapshot_invalid_source_and_units_fail() -> None:
    doc = json.loads(_fixture())
    doc["indicators"]["usd_idr"]["source_url"] = "file:///etc/passwd"
    with pytest.raises(ValueError, match="HTTPS"):
        parse_riil_market_snapshot(json.dumps(doc).encode())

    doc = json.loads(_fixture())
    doc["indicators"]["usd_idr"]["unit"] = "USD per IDR"
    with pytest.raises(ValueError, match="unit changed"):
        parse_riil_market_snapshot(json.dumps(doc).encode())


def test_market_snapshot_rejects_future_and_inconsistent_dates() -> None:
    doc = json.loads(_fixture())
    doc["updated_at"] = "2099-01-01"
    with pytest.raises(ValueError, match="future"):
        parse_riil_market_snapshot(json.dumps(doc).encode())

    doc = json.loads(_fixture())
    doc["indicators"]["usd_idr"]["as_of"] = "2026-10-19"
    with pytest.raises(ValueError, match="later than Riil updated_at"):
        parse_riil_market_snapshot(json.dumps(doc).encode())


def test_market_snapshot_preview_is_offline_and_no_database_needed(
    tmp_path, monkeypatch,
) -> None:
    input_file = tmp_path / "market-snapshot.json"
    input_file.write_bytes(_fixture())
    output_file = tmp_path / "safe-preview.json"
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert import_riil_market(
        input_file=input_file,
        persist_db=False,
        output_path=output_file,
    ) == 0
    preview = json.loads(output_file.read_text("utf-8"))
    assert len(preview["records"]) == 13
    assert preview["verification"] == "riil_curated_not_independently_verified"
    assert "should-not-appear" not in output_file.read_text("utf-8")
    assert "salary" not in output_file.read_text("utf-8")
