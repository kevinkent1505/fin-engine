from datetime import UTC, datetime
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from riil_analysis.database.config import normalize_database_url
from riil_analysis.database.models import (
    DataSource,
    IngestionRun,
    VehicleObservation,
    VehicleRecord,
)
from riil_analysis.ingestion.models import (
    CanonicalVehicleObservation,
    IngestionAudit,
    IngestionQualityReport,
)


def persist_ingestion(
    *,
    database_url: str,
    source_key: str,
    source_url: str,
    observations: list[CanonicalVehicleObservation],
    report: IngestionQualityReport,
    audit: IngestionAudit,
    started_at: datetime,
    authorization_reference: str | None,
    requested_limit: int | None,
    request_delay_seconds: float | None,
) -> dict[str, int | str]:
    engine = create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
    )

    run_id = str(uuid.uuid4())
    completed_at = datetime.now(UTC)
    inserted_observations = 0
    created_records = 0
    updated_records = 0

    with Session(engine) as session:
        source = session.get(DataSource, source_key)
        if source is None:
            source = DataSource(
                source_key=source_key,
                source_url=source_url,
                created_at=started_at,
            )
            session.add(source)
        else:
            source.source_url = source_url

        session.flush()

        session.add(
            IngestionRun(
                id=run_id,
                source_key=source_key,
                started_at=started_at,
                completed_at=completed_at,
                status="completed",
                authorization_reference=authorization_reference,
                requested_limit=requested_limit,
                request_delay_seconds=request_delay_seconds,
                quality=report.model_dump(mode="json"),
                audit=audit.model_dump(mode="json"),
            )
        )
        session.flush()

        for observation in observations:
            existing = session.scalar(
                select(VehicleRecord).where(
                    VehicleRecord.source_key == source_key,
                    VehicleRecord.source_record_id
                    == observation.source_record_id,
                )
            )

            if existing is None:
                vehicle_record = VehicleRecord(
                    id=str(uuid.uuid4()),
                    source_key=source_key,
                    source_record_id=observation.source_record_id,
                    source_url=observation.source_url,
                    make=observation.make,
                    model=observation.model,
                    variant=observation.variant,
                    type_name=observation.type_name,
                    year=observation.year,
                    region=observation.region,
                    category=observation.category,
                    first_seen_at=observation.observed_at,
                    last_seen_at=observation.observed_at,
                    latest_metadata=observation.metadata,
                )
                session.add(vehicle_record)
                session.flush()
                created_records += 1
            else:
                vehicle_record = existing
                vehicle_record.source_url = observation.source_url
                vehicle_record.make = observation.make
                vehicle_record.model = observation.model
                vehicle_record.variant = observation.variant
                vehicle_record.type_name = observation.type_name
                vehicle_record.year = observation.year
                vehicle_record.region = observation.region
                vehicle_record.category = observation.category
                vehicle_record.last_seen_at = max(
                    vehicle_record.last_seen_at,
                    observation.observed_at,
                )
                vehicle_record.latest_metadata = observation.metadata
                updated_records += 1

            session.add(
                VehicleObservation(
                    id=str(uuid.uuid4()),
                    vehicle_record_id=vehicle_record.id,
                    ingestion_run_id=run_id,
                    observed_at=observation.observed_at,
                    price=observation.price,
                    price_kind=observation.price_kind,
                    currency=observation.currency,
                    njkb=observation.njkb,
                    weight_factor=observation.weight_factor,
                    dp_pkb=observation.dp_pkb,
                    dp_pkb_expected=observation.dp_pkb_expected,
                    dp_pkb_difference=observation.dp_pkb_difference,
                    dp_pkb_check=observation.dp_pkb_check,
                    metadata_json=observation.metadata,
                )
            )
            inserted_observations += 1

        session.commit()

    engine.dispose()

    return {
        "run_id": run_id,
        "created_records": created_records,
        "updated_records": updated_records,
        "inserted_observations": inserted_observations,
    }
