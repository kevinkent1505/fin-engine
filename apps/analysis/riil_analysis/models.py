from typing import Literal

from pydantic import BaseModel, Field


class VehicleValuationRequest(BaseModel):
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1900, le=2100)
    region: str = Field(min_length=1, max_length=120)


class VehicleReferenceRequest(BaseModel):
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1900, le=2100)


class VehicleIdentity(BaseModel):
    make: str
    model: str
    year: int


class VehicleOption(BaseModel):
    make: str
    model: str
    year: int
    region: str


class VehicleCatalogResponse(BaseModel):
    vehicles: list[VehicleOption]
    source: str


class ValuationBand(BaseModel):
    estimate: int = Field(ge=0)
    low: int = Field(ge=0)
    high: int = Field(ge=0)


class VehicleValuationResponse(BaseModel):
    vehicle: VehicleIdentity
    region: str
    valuation: ValuationBand
    sample_size: int = Field(gt=0)
    method: str


class VehicleReferenceBand(BaseModel):
    status: Literal["exact", "range", "unavailable"]
    value: int | None = Field(default=None, ge=0)
    low: int | None = Field(default=None, ge=0)
    high: int | None = Field(default=None, ge=0)
    candidate_count: int = Field(ge=0)
    variants: list[str]
    source_keys: list[str]
    source_urls: list[str]


class VehicleReferenceResponse(BaseModel):
    vehicle: VehicleIdentity
    njkb: VehicleReferenceBand
    auction_limit: VehicleReferenceBand
