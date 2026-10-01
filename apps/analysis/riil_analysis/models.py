from pydantic import BaseModel, Field


class VehicleValuationRequest(BaseModel):
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1900, le=2100)
    region: str = Field(min_length=1, max_length=120)


class VehicleIdentity(BaseModel):
    make: str
    model: str
    year: int


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
