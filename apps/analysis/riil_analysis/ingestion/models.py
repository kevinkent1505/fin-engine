from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


PriceKind = Literal["listing", "transaction", "njkb", "reference"]
SemanticCheck = Literal["pass", "fail", "not_available"]


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

    njkb: int | None = None
    weight_factor: float | None = None
    dp_pkb: int | None = None
    dp_pkb_expected: int | None = None
    dp_pkb_difference: int | None = None
    dp_pkb_check: SemanticCheck = "not_available"

    metadata: dict[str, Any] = Field(default_factory=dict)


class RejectedRecord(BaseModel):
    source_record_id: str
    reason: str


class IngestionAudit(BaseModel):
    duplicate_record_ids: list[str] = Field(default_factory=list)
    rejected_records: list[RejectedRecord] = Field(default_factory=list)
    semantic_failure_record_ids: list[str] = Field(default_factory=list)


class IngestionQualityReport(BaseModel):
    source: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    missing_price_records: int = 0
    invalid_year_records: int = 0
    normalization_failures: int = 0

    semantic_checks_total: int = 0
    semantic_checks_passed: int = 0
    semantic_checks_failed: int = 0
    semantic_checks_skipped: int = 0
