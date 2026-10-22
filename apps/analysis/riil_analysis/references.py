from sqlalchemy import and_, create_engine, func, select
from sqlalchemy.orm import Session

from .database.config import normalize_database_url
from .database.models import DataSource, VehicleObservation, VehicleRecord
from .models import (
    VehicleIdentity,
    VehicleReferenceBand,
    VehicleReferenceRequest,
    VehicleReferenceResponse,
)


def _reference_band(
    *,
    database_url: str,
    request: VehicleReferenceRequest,
    price_kind: str,
) -> VehicleReferenceBand:
    """Resolve official/reference values without inventing a variant match."""
    engine = create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
    )

    latest_observation = (
        select(
            VehicleObservation.vehicle_record_id.label("vehicle_record_id"),
            func.max(VehicleObservation.observed_at).label("latest_observed_at"),
        )
        .where(VehicleObservation.price_kind == price_kind)
        .group_by(VehicleObservation.vehicle_record_id)
        .subquery()
    )

    statement = (
        select(
            VehicleObservation.price,
            VehicleRecord.variant,
            VehicleRecord.source_key,
            DataSource.source_url,
        )
        .join(
            VehicleRecord,
            VehicleRecord.id == VehicleObservation.vehicle_record_id,
        )
        .join(
            latest_observation,
            and_(
                latest_observation.c.vehicle_record_id
                == VehicleObservation.vehicle_record_id,
                latest_observation.c.latest_observed_at
                == VehicleObservation.observed_at,
            ),
        )
        .join(DataSource, DataSource.source_key == VehicleRecord.source_key)
        .where(
            func.lower(VehicleRecord.make) == request.make.strip().lower(),
            func.lower(VehicleRecord.model) == request.model.strip().lower(),
            VehicleRecord.year == request.year,
            VehicleObservation.price_kind == price_kind,
        )
        .order_by(VehicleObservation.price)
    )

    try:
        with Session(engine) as session:
            rows = session.execute(statement).all()
    finally:
        engine.dispose()

    if not rows:
        return VehicleReferenceBand(
            status="unavailable",
            candidate_count=0,
            variants=[],
            source_keys=[],
            source_urls=[],
        )

    prices = sorted({int(row.price) for row in rows})
    variants = sorted(
        {
            str(row.variant).strip()
            for row in rows
            if row.variant is not None and str(row.variant).strip()
        }
    )
    source_keys = sorted({str(row.source_key) for row in rows})
    source_urls = sorted({str(row.source_url) for row in rows})

    if len(prices) == 1:
        value = prices[0]
        return VehicleReferenceBand(
            status="exact",
            value=value,
            low=value,
            high=value,
            candidate_count=len(rows),
            variants=variants,
            source_keys=source_keys,
            source_urls=source_urls,
        )

    return VehicleReferenceBand(
        status="range",
        low=prices[0],
        high=prices[-1],
        candidate_count=len(rows),
        variants=variants,
        source_keys=source_keys,
        source_urls=source_urls,
    )


def resolve_vehicle_references(
    request: VehicleReferenceRequest,
    database_url: str,
) -> VehicleReferenceResponse:
    """Return NJKB and auction reference coverage for one make/model/year."""
    return VehicleReferenceResponse(
        vehicle=VehicleIdentity(
            make=request.make,
            model=request.model,
            year=request.year,
        ),
        njkb=_reference_band(
            database_url=database_url,
            request=request,
            price_kind="njkb",
        ),
        auction_limit=_reference_band(
            database_url=database_url,
            request=request,
            price_kind="auction_limit",
        ),
    )
