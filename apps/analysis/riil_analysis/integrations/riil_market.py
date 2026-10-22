"""Inbound adapter for Riil's already-published *market* snapshot.

This is a deliberately limited public-data integration. It never queries
Riil's D1, tracker, accounts, calculations or private GitHub repository.
Every stored number remains attributed to its original cited publisher.
"""
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

RIIL_MARKET_SNAPSHOT_URL = "https://riil.id/data/market-snapshot.json"
SOURCE_KEY = "riil_published_market_snapshot_v1"
MAX_BYTES = 256_000

# Only editorially published market indicators; never introspect arbitrary
# JSON keys into the database or accept data from tracker/account endpoints.
SIMPLE = {
    "usd_idr": ("IDR per USD", Decimal("5000"), Decimal("50000")),
    "inflation_yoy": ("percent, year on year", Decimal("-10"), Decimal("50")),
    "oil_icp": ("USD per barrel", Decimal("5"), Decimal("500")),
    "ihsg": (None, Decimal("1000"), Decimal("30000")),
}
FUEL_GRADES = {
    "pertalite", "pertamax", "pertamax_green", "pertamax_turbo",
    "dexlite", "pertamina_dex",
}
REQUIRED = {*SIMPLE, "fuel", "gold_antam"}


@dataclass(frozen=True)
class RiilIndicator:
    code: str
    as_of: date
    value: Decimal
    unit: str
    original_publisher: str
    original_source_url: str
    revision_sha256: str
    metadata: dict[str, str | bool]


@dataclass(frozen=True)
class RiilMarketSnapshot:
    snapshot_sha256: str
    updated_at: date
    observations: tuple[RiilIndicator, ...]


def fetch_riil_market_snapshot(*, input_file: Path | None = None) -> bytes:
    """Explicit, read-only acquisition from a fixed public Riil URL."""
    if input_file is not None:
        if input_file.suffix.lower() != ".json":
            raise ValueError("Riil market import accepts .json files only.")
        payload = input_file.read_bytes()
    else:
        with httpx.Client(
            follow_redirects=False,
            timeout=30,
            headers={"Accept": "application/json", "User-Agent": "FinEngine/0.1"},
        ) as client:
            response = client.get(RIIL_MARKET_SNAPSHOT_URL)
            response.raise_for_status()
            payload = response.content
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("Riil market snapshot is empty or exceeds 256 KB.")
    return payload


def _calendar_date(raw: Any, field: str) -> date:
    if not isinstance(raw, str):
        raise ValueError(f"{field} must be an ISO YYYY-MM-DD date.")
    try:
        value = date.fromisoformat(raw)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO YYYY-MM-DD date.") from error
    if value.isoformat() != raw or value > datetime.now(UTC).date():
        raise ValueError(f"{field} is malformed or in the future.")
    return value


def _number(raw: Any, field: str, low: Decimal, high: Decimal) -> Decimal:
    if isinstance(raw, bool) or not isinstance(raw, (float, int)):
        raise ValueError(f"{field} must be a numeric market indicator.")
    try:
        value = Decimal(str(raw))
    except InvalidOperation as error:
        raise ValueError(f"{field} has an invalid numeric value.") from error
    if not value.is_finite() or not low <= value <= high:
        raise ValueError(f"{field} is outside its approved range.")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field} exceeds six decimal places.")
    return value


def _original_source(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or len(raw) > 2048:
        raise ValueError(f"{field} must be a source URL.")
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username:
        raise ValueError(f"{field} must be an HTTPS source URL.")
    return raw


def _make_indicator(
    *,
    code: str,
    value: Any,
    as_of: date,
    unit: str,
    publisher: str,
    source_url: str,
    updated_at: date,
    low: Decimal,
    high: Decimal,
) -> RiilIndicator:
    if not isinstance(publisher, str) or not publisher.strip() or len(publisher) > 255:
        raise ValueError(f"{code} is missing original source attribution.")
    if not isinstance(unit, str) or not unit or len(unit) > 80:
        raise ValueError(f"{code} has no supported unit.")
    checked_source_url = _original_source(source_url, code + ".source_url")
    parsed_value = _number(value, code, low, high)
    canonical = {
        "indicator": code,
        "value": str(parsed_value.normalize()),
        "unit": unit,
        "as_of": as_of.isoformat(),
        "original_publisher": publisher.strip(),
        "original_source_url": checked_source_url,
    }
    revision_sha256 = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return RiilIndicator(
        code=code,
        value=parsed_value,
        as_of=as_of,
        unit=unit,
        original_publisher=publisher.strip(),
        original_source_url=checked_source_url,
        revision_sha256=revision_sha256,
        metadata={
            "origin_product": "riil",
            "origin_type": "editorial_published_market_snapshot",
            "riil_updated_at": updated_at.isoformat(),
            "verification": "not_independently_verified_by_fin_engine",
        },
    )


def parse_riil_market_snapshot(payload: bytes) -> RiilMarketSnapshot:
    """Fail closed on missing/out-of-range data before any DB write."""
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("Riil market snapshot is empty or exceeds 256 KB.")
    try:
        doc = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Riil market snapshot is not valid JSON.") from error
    if not isinstance(doc, dict) or not isinstance(doc.get("indicators"), dict):
        raise ValueError("Riil market snapshot must contain indicators object.")

    updated_at = _calendar_date(doc.get("updated_at"), "updated_at")
    data = doc["indicators"]
    missing = REQUIRED - set(data)
    if missing:
        raise ValueError(f"Riil market snapshot is incomplete: {sorted(missing)}.")

    records: list[RiilIndicator] = []

    def append(
        code: str,
        raw_value: Any,
        obj: dict,
        unit: str,
        bounds: tuple[Decimal, Decimal],
        *,
        value_date: str = "as_of",
        publisher_field: str = "source_name",
        url_field: str = "source_url",
    ) -> None:
        as_of = _calendar_date(obj.get(value_date), code + "." + value_date)
        # Corrected old periods can be republished later, but never a future
        # reference date or a period later than the snapshot itself.
        if as_of > updated_at:
            raise ValueError(f"{code} has as_of later than Riil updated_at.")
        records.append(_make_indicator(
            code=code,
            value=raw_value,
            as_of=as_of,
            unit=unit,
            publisher=obj.get(publisher_field),
            source_url=obj.get(url_field),
            updated_at=updated_at,
            low=bounds[0],
            high=bounds[1],
        ))

    for code, (expected_unit, lower, upper) in SIMPLE.items():
        obj = data[code]
        if not isinstance(obj, dict):
            raise ValueError(f"{code} must be an object.")
        unit = obj.get("unit", expected_unit)
        if unit != expected_unit and expected_unit is not None:
            raise ValueError(f"{code} unit changed; review adapter before importing.")
        if expected_unit is None:
            unit = "index_points"
        append(code, obj.get("value"), obj, unit, (lower, upper))

    gold = data["gold_antam"]
    if not isinstance(gold, dict) or gold.get("unit") != "IDR per gram":
        raise ValueError("gold_antam units are not supported.")
    for key in ("price", "buyback"):
        append(
            "gold_antam_" + key, gold.get(key), gold, "IDR per gram",
            (Decimal("100000"), Decimal("50000000"))
        )

    fuel = data["fuel"]
    if not isinstance(fuel, dict) or fuel.get("unit") != "IDR per litre":
        raise ValueError("fuel units are not supported.")
    prices = fuel.get("prices")
    if not isinstance(prices, dict) or set(prices) != FUEL_GRADES:
        raise ValueError("fuel prices do not match approved grade keys.")
    for grade in sorted(FUEL_GRADES):
        append(
            "fuel_" + grade, prices[grade], fuel, "IDR per litre",
            (Decimal("1000"), Decimal("100000"))
        )

    ihsg = data["ihsg"]
    if "previous" in ihsg:
        append(
            "ihsg_previous", ihsg.get("previous"), ihsg, "index_points",
            (Decimal("1000"), Decimal("30000")),
            value_date="previous_as_of", publisher_field="previous_source_name",
            url_field="previous_source_url",
        )

    codes = [item.code for item in records]
    if len(codes) != len(set(codes)) or len(records) < 12:
        raise ValueError("Riil market snapshot has duplicate/incomplete indicators.")

    return RiilMarketSnapshot(
        snapshot_sha256=hashlib.sha256(payload).hexdigest(),
        updated_at=updated_at,
        observations=tuple(records),
    )
