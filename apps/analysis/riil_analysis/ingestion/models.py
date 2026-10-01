from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


PriceKind = Literal["listing", "transaction", "njkb", "reference"]


class RawVehicleObservation(BaseModel):
    source: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    observed_at: datetime

    make_raw: str | None = None
    model_raw: str | None = None
    variant_raw: str | None = None
    type_raw: str | None = None
    year_raw: str | int | None = None
    region_raw: str | None = None
    price_raw: str | int | None = None

    price_kind: PriceKind
    currency: str = "IDR"
    category_raw: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonicalVehicleObservation(BaseModel):
    source: str
    source_record_id: str
    source_url: str
    observed_at: datetime

    make: str
    model: str | None = None
    variant: str | None = None
    type_name: str | None = None
    year: int
    region: str
    price: int

    price_kind: PriceKind
    currency: str
    category: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionQualityReport(BaseModel):
    source: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    missing_price_records: int = 0
    invalid_year_records: int = 0
    normalization_failures: int = 0
