from functools import lru_cache
from pathlib import Path

import polars as pl

from .models import (
    ValuationBand,
    VehicleIdentity,
    VehicleValuationRequest,
    VehicleValuationResponse,
)


@lru_cache(maxsize=8)
def load_vehicle_data(data_path: str) -> pl.DataFrame:
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Vehicle dataset not found: {path}")

    return pl.read_csv(path).with_columns(
        pl.col("make").str.strip_chars().str.to_lowercase().alias("_make_key"),
        pl.col("model").str.strip_chars().str.to_lowercase().alias("_model_key"),
        pl.col("region").str.strip_chars().str.to_lowercase().alias("_region_key"),
    )


def estimate_vehicle_value(
    request: VehicleValuationRequest,
    data_path: str,
) -> VehicleValuationResponse:
    data = load_vehicle_data(data_path)

    comparables = data.filter(
        (pl.col("_make_key") == request.make.strip().lower())
        & (pl.col("_model_key") == request.model.strip().lower())
        & (pl.col("year") == request.year)
        & (pl.col("_region_key") == request.region.strip().lower())
    )

    if comparables.is_empty():
        raise ValueError("No comparable vehicle observations were found.")

    prices = comparables.get_column("price").sort()
    estimate = prices.median()
    low = prices.quantile(0.10, interpolation="nearest")
    high = prices.quantile(0.90, interpolation="nearest")

    if estimate is None or low is None or high is None:
        raise ValueError("Comparable observations did not contain valid prices.")

    return VehicleValuationResponse(
        vehicle=VehicleIdentity(
            make=request.make,
            model=request.model,
            year=request.year,
        ),
        region=request.region,
        valuation=ValuationBand(
            estimate=int(estimate),
            low=int(low),
            high=int(high),
        ),
        sample_size=comparables.height,
        method="comparable_market_v1",
    )
