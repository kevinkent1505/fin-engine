import re
from typing import Any

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

# Conservative first-pass exceptions. The method is explicitly recorded
# as heuristic and is not intended to replace a future vehicle master.
MULTI_TOKEN_MODEL_PREFIXES = (
    "LAND CRUISER",
    "GRAND LIVINA",
    "PAJERO SPORT",
    "CITY HATCHBACK",
    "CIVIC TYPE R",
    "RANGE ROVER",
)


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


def normalize_decimal(value: str | int | float | None) -> float | None:
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    cleaned = re.sub(r"\s+", "", str(value)).replace(",", ".")
    if cleaned.count(".") > 1:
        raise ValueError(f"Invalid decimal value: {value!r}")

    try:
        return float(cleaned)
    except ValueError as error:
        raise ValueError(f"Invalid decimal value: {value!r}") from error


def normalize_region(value: str | None) -> str:
    cleaned = clean_text(value)
    return cleaned.title() if cleaned else "Indonesia"


def normalize_category(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if not cleaned:
        return None

    cleaned = re.sub(r"\s*-\s*", " - ", cleaned)
    return " ".join(cleaned.split())


def normalize_regulation(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if not cleaned:
        return None

    cleaned = re.sub(r"(?<=\d)(?=Tahun\b)", " ", cleaned)
    return " ".join(cleaned.split())


def infer_model_variant(
    model_raw: str | None,
    variant_raw: str | None,
    type_raw: str | None,
) -> tuple[str | None, str | None, str | None, float | None]:
    model = clean_text(model_raw)
    variant = clean_text(variant_raw)

    if model:
        return model, variant, "source_fields", 1.0

    type_name = clean_text(type_raw)
    if not type_name:
        return None, variant, None, None

    # Homologation/model codes in parentheses are source metadata, not
    # customer-facing model/variant names.
    descriptor = re.sub(r"\s*\([^)]*\)\s*$", "", type_name).strip()
    upper = descriptor.upper()

    for prefix in MULTI_TOKEN_MODEL_PREFIXES:
        if upper == prefix or upper.startswith(prefix + " "):
            remainder = descriptor[len(prefix):].strip() or None
            return prefix.title(), remainder, "heuristic_type_prefix_v1", 0.75

    first, *rest = descriptor.split(" ", 1)
    remainder = rest[0] if rest else None

    # This is deliberately labelled as a candidate. A future vehicle master
    # will replace this heuristic with proper entity resolution.
    return first.title(), remainder, "heuristic_first_token_v1", 0.60


def reference_fields(
    raw: RawVehicleObservation,
    *,
    normalized_price: int,
) -> tuple[
    int | None,
    float | None,
    int | None,
    int | None,
    int | None,
    str,
    dict[str, Any],
]:
    metadata = dict(raw.metadata)

    regulation_raw = metadata.get("regulation")
    weight_raw = metadata.get("weight")
    dp_pkb_raw = metadata.get("dp_pkb")

    if regulation_raw is not None:
        metadata["regulation_raw"] = regulation_raw
        metadata["regulation"] = normalize_regulation(str(regulation_raw))

    if weight_raw is not None:
        metadata["weight_raw"] = weight_raw

    if dp_pkb_raw is not None:
        metadata["dp_pkb_raw"] = dp_pkb_raw

    if raw.price_kind != "njkb":
        return None, None, None, None, None, "not_available", metadata

    njkb = normalized_price
    weight_factor = normalize_decimal(weight_raw)
    dp_pkb = (
        normalize_price(str(dp_pkb_raw))
        if dp_pkb_raw not in (None, "")
        else None
    )

    if weight_factor is None or dp_pkb is None:
        return (
            njkb,
            weight_factor,
            dp_pkb,
            None,
            None,
            "not_available",
            metadata,
        )

    expected = int(round(njkb * weight_factor))
    difference = abs(dp_pkb - expected)

    # Official tables are normally exact to the rupiah/thousand. A small
    # Rp1,000 allowance avoids false failures from displayed rounding.
    check = "pass" if difference <= 1_000 else "fail"

    return (
        njkb,
        weight_factor,
        dp_pkb,
        expected,
        difference,
        check,
        metadata,
    )


def normalize_vehicle_observation(
    raw: RawVehicleObservation,
) -> CanonicalVehicleObservation:
    price = normalize_price(raw.price_raw)
    model, variant, resolution_method, resolution_confidence = (
        infer_model_variant(
            raw.model_raw,
            raw.variant_raw,
            raw.type_raw,
        )
    )

    (
        njkb,
        weight_factor,
        dp_pkb,
        dp_pkb_expected,
        dp_pkb_difference,
        dp_pkb_check,
        metadata,
    ) = reference_fields(raw, normalized_price=price)

    if resolution_method:
        metadata["model_resolution_method"] = resolution_method
        metadata["model_resolution_confidence"] = resolution_confidence

    return CanonicalVehicleObservation(
        source=raw.source,
        source_record_id=raw.source_record_id,
        source_url=raw.source_url,
        observed_at=raw.observed_at,
        make=normalize_make(raw.make_raw),
        model=model,
        variant=variant,
        type_name=clean_text(raw.type_raw),
        year=normalize_year(raw.year_raw),
        region=normalize_region(raw.region_raw),
        price=price,
        price_kind=raw.price_kind,
        currency=raw.currency.upper(),
        category=normalize_category(raw.category_raw),
        njkb=njkb,
        weight_factor=weight_factor,
        dp_pkb=dp_pkb,
        dp_pkb_expected=dp_pkb_expected,
        dp_pkb_difference=dp_pkb_difference,
        dp_pkb_check=dp_pkb_check,
        metadata=metadata,
    )
