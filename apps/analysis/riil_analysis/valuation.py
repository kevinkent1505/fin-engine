from functools import lru_cache
from pathlib import Path
from statistics import median

import polars as pl
from sqlalchemy import and_, create_engine, func, select
from sqlalchemy.orm import Session

from .database.config import normalize_database_url
from .database.models import VehicleObservation, VehicleRecord
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


def _nearest_quantile(values: list[int], quantile: float) -> int:
    if not values:
        raise ValueError("Comparable observations did not contain valid prices.")

    ordered = sorted(values)
    index = round((len(ordered) - 1) * quantile)
    return ordered[index]


def _valuation_response(
    request: VehicleValuationRequest,
    prices: list[int],
    *,
    method: str,
) -> VehicleValuationResponse:
    if not prices:
        raise ValueError("No comparable vehicle observations were found.")

    ordered = sorted(prices)
    estimate = int(median(ordered))
    low = _nearest_quantile(ordered, 0.10)
    high = _nearest_quantile(ordered, 0.90)

    return VehicleValuationResponse(
        vehicle=VehicleIdentity(
            make=request.make,
            model=request.model,
            year=request.year,
        ),
        region=request.region,
        valuation=ValuationBand(
            estimate=estimate,
            low=low,
            high=high,
        ),
        sample_size=len(ordered),
        method=method,
    )


def estimate_vehicle_value(
    request: VehicleValuationRequest,
    data_path: str,
) -> VehicleValuationResponse:
    """Development valuation path backed by the committed comparable CSV."""
    data = load_vehicle_data(data_path)

    comparables = data.filter(
        (pl.col("_make_key") == request.make.strip().lower())
        & (pl.col("_model_key") == request.model.strip().lower())
        & (pl.col("year") == request.year)
        & (pl.col("_region_key") == request.region.strip().lower())
    )

    if comparables.is_empty():
        raise ValueError("No comparable vehicle observations were found.")

    return _valuation_response(
        request,
        [int(value) for value in comparables.get_column("price").to_list()],
        method="comparable_market_v1",
    )


def estimate_vehicle_value_from_database(
    request: VehicleValuationRequest,
    database_url: str,
) -> VehicleValuationResponse:
    """
    Estimate asking value from the latest listing observation per source record.

    Repeated crawler observations are intentionally retained in PostgreSQL, but
    a valuation snapshot must not overweight a listing merely because it was
    observed many times. This query therefore selects only the latest listing
    observation for each stable vehicle_record.
    """
    engine = create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
    )

    latest_listing = (
        select(
            VehicleObservation.vehicle_record_id.label("vehicle_record_id"),
            func.max(VehicleObservation.observed_at).label("latest_observed_at"),
        )
        .where(VehicleObservation.price_kind == "listing")
        .group_by(VehicleObservation.vehicle_record_id)
        .subquery()
    )

    statement = (
        select(VehicleObservation.price)
        .join(
            VehicleRecord,
            VehicleRecord.id == VehicleObservation.vehicle_record_id,
        )
        .join(
            latest_listing,
            and_(
                latest_listing.c.vehicle_record_id
                == VehicleObservation.vehicle_record_id,
                latest_listing.c.latest_observed_at
                == VehicleObservation.observed_at,
            ),
        )
        .where(
            func.lower(VehicleRecord.make) == request.make.strip().lower(),
            func.lower(VehicleRecord.model) == request.model.strip().lower(),
            VehicleRecord.year == request.year,
            func.lower(VehicleRecord.region) == request.region.strip().lower(),
            VehicleObservation.price_kind == "listing",
        )
    )

    try:
        with Session(engine) as session:
            prices = [int(value) for value in session.scalars(statement).all()]
    finally:
        engine.dispose()

    return _valuation_response(
        request,
        prices,
        method="comparable_market_db_v1",
    )
