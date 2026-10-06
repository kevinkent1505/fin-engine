from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from .database.config import normalize_database_url
from .database.models import VehicleObservation, VehicleRecord
from .models import VehicleOption


def list_official_vehicle_options(database_url: str) -> list[VehicleOption]:
    """Return distinct vehicle selections backed by persisted official NJKB data."""
    engine = create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
    )

    statement = (
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
        .order_by(
            func.lower(VehicleRecord.make),
            func.lower(VehicleRecord.model),
            VehicleRecord.year.desc(),
        )
    )

    try:
        with Session(engine) as session:
            rows = session.execute(statement).all()
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
