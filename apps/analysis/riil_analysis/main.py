import os

from fastapi import FastAPI, HTTPException

from .models import (
    VehicleCatalogResponse,
    VehicleValuationRequest,
    VehicleValuationResponse,
)
from .regional import (
    RegionalMarketResponse,
    latest_regional_market_from_database,
)
from .valuation import (
    database_listing_catalog_source,
    estimate_vehicle_value,
    estimate_vehicle_value_from_database,
    list_available_vehicles,
    list_available_vehicles_from_database,
)

app = FastAPI(title="Fin Engine Analysis", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "analysis"}


@app.get(
    "/internal/v1/vehicles/options",
    response_model=VehicleCatalogResponse,
)
def vehicle_options() -> VehicleCatalogResponse:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return VehicleCatalogResponse(
            vehicles=list_available_vehicles_from_database(database_url),
            source=database_listing_catalog_source(database_url),
        )

    data_path = os.getenv(
        "VEHICLE_DATA_PATH",
        "../../data/sample/vehicles.csv",
    )
    return VehicleCatalogResponse(
        vehicles=list_available_vehicles(data_path),
        source="development",
    )


@app.get(
    "/internal/v1/regional-market",
    response_model=RegionalMarketResponse,
)
def regional_market() -> RegionalMarketResponse:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is required for persisted regional statistics.",
        )

    try:
        return latest_regional_market_from_database(database_url)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/internal/v1/vehicles/valuation",
    response_model=VehicleValuationResponse,
)
def vehicle_valuation(
    request: VehicleValuationRequest,
) -> VehicleValuationResponse:
    database_url = os.getenv("DATABASE_URL")

    try:
        if database_url:
            return estimate_vehicle_value_from_database(
                request=request,
                database_url=database_url,
            )

        data_path = os.getenv(
            "VEHICLE_DATA_PATH",
            "../../data/sample/vehicles.csv",
        )
        return estimate_vehicle_value(request=request, data_path=data_path)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
