import re

from riil_analysis.ingestion.models import (
    CanonicalVehicleObservation,
    RawVehicleObservation,
)


MAKE_ALIASES = {
    "AUDI": "Audi",
    "BMW": "BMW",
    "BYD": "BYD",
    "DAIHATSU": "Daihatsu",
    "HONDA": "Honda",
    "HYUNDAI": "Hyundai",
    "ISUZU": "Isuzu",
    "LEXUS": "Lexus",
    "MAZDA": "Mazda",
    "MERCEDES BENZ": "Mercedes-Benz",
    "MERCEDES-BENZ": "Mercedes-Benz",
    "MITSUBISHI": "Mitsubishi",
    "NISSAN": "Nissan",
    "SUZUKI": "Suzuki",
    "TOYOTA": "Toyota",
    "VOLKSWAGEN": "Volkswagen",
    "WULING": "Wuling",
}


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(value.replace("\n", " ").split())
    return cleaned or None


def normalize_make(value: str | None) -> str:
    cleaned = clean_text(value)
    if not cleaned:
        raise ValueError("Vehicle make is missing.")

    upper = cleaned.upper()
    return MAKE_ALIASES.get(upper, cleaned.title())


def normalize_year(value: str | int | None) -> int:
    if value is None:
        raise ValueError("Vehicle year is missing.")

    match = re.search(r"\b(19\d{2}|20\d{2}|2100)\b", str(value))
    if not match:
        raise ValueError(f"Invalid vehicle year: {value!r}")

    return int(match.group(1))


def normalize_price(value: str | int | None) -> int:
    if value is None:
        raise ValueError("Vehicle price is missing.")

    if isinstance(value, int):
        if value < 0:
            raise ValueError("Vehicle price cannot be negative.")
        return value

    digits = re.sub(r"[^0-9]", "", value)
    if not digits:
        raise ValueError(f"Invalid vehicle price: {value!r}")

    price = int(digits)
    if price < 0:
        raise ValueError("Vehicle price cannot be negative.")

    return price


def normalize_region(value: str | None) -> str:
    cleaned = clean_text(value)
    return cleaned.title() if cleaned else "Indonesia"


def normalize_vehicle_observation(
    raw: RawVehicleObservation,
) -> CanonicalVehicleObservation:
    return CanonicalVehicleObservation(
        source=raw.source,
        source_record_id=raw.source_record_id,
        source_url=raw.source_url,
        observed_at=raw.observed_at,
        make=normalize_make(raw.make_raw),
        model=clean_text(raw.model_raw),
        variant=clean_text(raw.variant_raw),
        type_name=clean_text(raw.type_raw),
        year=normalize_year(raw.year_raw),
        region=normalize_region(raw.region_raw),
        price=normalize_price(raw.price_raw),
        price_kind=raw.price_kind,
        currency=raw.currency.upper(),
        category=clean_text(raw.category_raw),
        metadata=raw.metadata,
    )
