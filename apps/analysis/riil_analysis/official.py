from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from .database.config import normalize_database_url
from .database.models import VehicleObservation, VehicleRecord
from .models import VehicleOption


def _official_vehicle_options_statement():
    """Deduplicate official selections before applying case-insensitive ordering.

    PostgreSQL requires ORDER BY expressions to appear in a SELECT DISTINCT's
    projection. Ordering the outer query avoids that restriction while keeping
    make/model/year identity and case-insensitive display ordering.
    """
    distinct_vehicles = (
        select(
            VehicleRecord.make,
            VehicleRecord.model,
            VehicleRecord.year,
        )
        .join(
            VehicleObservation,
            VehicleObservation.vehicle_record_id == VehicleRecord.id,
        )
        .where(
            VehicleRecord.model.is_not(None),
            VehicleObservation.price_kind == "njkb",
        )
        .distinct()
        .subquery()
    )

    return (
        select(
            distinct_vehicles.c.make,
            distinct_vehicles.c.model,
            distinct_vehicles.c.year,
        )
        .order_by(
            func.lower(distinct_vehicles.c.make),
            func.lower(distinct_vehicles.c.model),
            distinct_vehicles.c.year.desc(),
        )
    )


def list_official_vehicle_options(database_url: str) -> list[VehicleOption]:
    """Return distinct vehicle selections backed by persisted official NJKB data."""
    engine = create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
    )

    try:
        with Session(engine) as session:
            rows = session.execute(_official_vehicle_options_statement()).all()
    finally:
        engine.dispose()

    return [
        VehicleOption(
            make=str(make),
            model=str(model),
            year=int(year),
            region="Indonesia",
        )
        for make, model, year in rows
        if model is not None
    ]
