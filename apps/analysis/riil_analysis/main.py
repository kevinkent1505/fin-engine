import os

from fastapi import FastAPI, HTTPException

from .models import VehicleValuationRequest, VehicleValuationResponse
from .valuation import estimate_vehicle_value

app = FastAPI(title="Fin Engine Analysis", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "analysis"}


@app.post(
    "/internal/v1/vehicles/valuation",
    response_model=VehicleValuationResponse,
)
def vehicle_valuation(
    request: VehicleValuationRequest,
) -> VehicleValuationResponse:
    data_path = os.getenv(
        "VEHICLE_DATA_PATH",
        "../../data/sample/vehicles.csv",
    )

    try:
        return estimate_vehicle_value(request=request, data_path=data_path)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
