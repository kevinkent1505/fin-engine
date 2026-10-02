from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .database.config import normalize_database_url
from .database.models import IngestionRun, RegionalVehicleStatistic


BPS_VEHICLE_STOCK_SOURCE = "bps_vehicle_stock_2025"


class RegionalVehicleStatisticInput(BaseModel):
    source: str
    source_url: str
    observed_at: datetime
    year: int = Field(ge=1900, le=2100)
    region: str = Field(min_length=1, max_length=200)
    passenger_cars: int = Field(ge=0)
    buses: int = Field(ge=0)
    trucks: int = Field(ge=0)
    motorcycles: int = Field(ge=0)
    total: int = Field(ge=0)
    metadata: dict = Field(default_factory=dict)


class RegionalMarketPoint(BaseModel):
    region: str
    passenger_cars: int = Field(ge=0)


class RegionalMarketResponse(BaseModel):
    source: str
    source_url: str
    year: int
    observed_at: datetime
    regions: list[RegionalMarketPoint]


def latest_regional_market_from_database(
    database_url: str,
    *,
    source_key: str = BPS_VEHICLE_STOCK_SOURCE,
    limit: int = 7,
) -> RegionalMarketResponse:
    """Return the latest persisted official regional passenger-car snapshot."""
    engine = create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
    )

    try:
        with Session(engine) as session:
            latest_run = session.scalar(
                select(IngestionRun)
                .where(
                    IngestionRun.source_key == source_key,
                    IngestionRun.status == "completed",
                )
                .order_by(IngestionRun.completed_at.desc())
                .limit(1)
            )
            if latest_run is None:
                raise ValueError(
                    f"No completed regional statistics ingestion exists for {source_key}."
                )

            rows = session.scalars(
                select(RegionalVehicleStatistic)
                .where(
                    RegionalVehicleStatistic.ingestion_run_id == latest_run.id,
                    RegionalVehicleStatistic.region != "Indonesia",
                )
                .order_by(RegionalVehicleStatistic.passenger_cars.desc())
                .limit(limit)
            ).all()

            if not rows:
                raise ValueError("No regional vehicle statistics were found.")

            first = rows[0]
            return RegionalMarketResponse(
                source=source_key,
                source_url=first.source_url,
                year=first.year,
                observed_at=max(row.observed_at for row in rows),
                regions=[
                    RegionalMarketPoint(
                        region=row.region,
                        passenger_cars=row.passenger_cars,
                    )
                    for row in rows
                ],
            )
    finally:
        engine.dispose()
