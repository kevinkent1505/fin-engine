"""Transactional persistence for independent market-indicator observations."""
from datetime import UTC, datetime
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from riil_analysis.database.config import normalize_database_url
from riil_analysis.database.models import (
    DataSource, IngestionRun, MarketIndicatorObservation,
)
from riil_analysis.integrations.riil_market import (
    RIIL_MARKET_SNAPSHOT_URL, SOURCE_KEY, RiilMarketSnapshot,
)


def persist_riil_market_snapshot(
    *, database_url: str, snapshot: RiilMarketSnapshot,
) -> dict[str, int | str | None]:
    """Append new semantic revisions; an identical replay changes no rows.

    First validate the complete source outside this function. One transaction
    inserts the source, run and new observations together; a failure rolls
    back the entire import. No Riil application endpoint is modified.
    """
    engine = create_engine(
        normalize_database_url(database_url), pool_pre_ping=True,
    )
    try:
        with Session(engine) as session:
            existing = set(session.execute(
                select(
                    MarketIndicatorObservation.indicator_code,
                    MarketIndicatorObservation.as_of,
                    MarketIndicatorObservation.revision_sha256,
                ).where(MarketIndicatorObservation.source_key == SOURCE_KEY)
            ).all())
            new = [
                item for item in snapshot.observations
                if (item.code, item.as_of, item.revision_sha256) not in existing
            ]
            if not new:
                return {
                    "run_id": None,
                    "inserted_observations": 0,
                    "skipped_existing": len(snapshot.observations),
                }

            now = datetime.now(UTC)
            source = session.get(DataSource, SOURCE_KEY)
            if source is None:
                session.add(DataSource(
                    source_key=SOURCE_KEY,
                    source_url=RIIL_MARKET_SNAPSHOT_URL,
                    created_at=now,
                ))
            else:
                source.source_url = RIIL_MARKET_SNAPSHOT_URL
            session.flush()

            run_id = str(uuid.uuid4())
            session.add(IngestionRun(
                id=run_id,
                source_key=SOURCE_KEY,
                started_at=now,
                completed_at=now,
                status="completed",
                authorization_reference=None,
                requested_limit=None,
                request_delay_seconds=None,
                quality={
                    "source": SOURCE_KEY,
                    "total_records": len(snapshot.observations),
                    "valid_records": len(snapshot.observations),
                    "invalid_records": 0,
                },
                audit={
                    "dataset_type": "market_indicator_observations",
                    "origin_product": "riil",
                    "acquisition": "published_public_snapshot",
                    "independently_verified": False,
                    "snapshot_sha256": snapshot.snapshot_sha256,
                    "riil_updated_at": snapshot.updated_at.isoformat(),
                    "inserted_observations": len(new),
                    "skipped_existing": len(snapshot.observations) - len(new),
                },
            ))
            session.flush()

            for record in new:
                session.add(MarketIndicatorObservation(
                    id=str(uuid.uuid4()),
                    source_key=SOURCE_KEY,
                    ingestion_run_id=run_id,
                    indicator_code=record.code,
                    as_of=record.as_of,
                    value=record.value,
                    unit=record.unit,
                    original_publisher=record.original_publisher,
                    original_source_url=record.original_source_url,
                    origin_snapshot_url=RIIL_MARKET_SNAPSHOT_URL,
                    snapshot_sha256=snapshot.snapshot_sha256,
                    revision_sha256=record.revision_sha256,
                    imported_at=now,
                    metadata_json=record.metadata,
                ))
            session.commit()
            return {
                "run_id": run_id,
                "inserted_observations": len(new),
                "skipped_existing": len(snapshot.observations) - len(new),
            }
    finally:
        engine.dispose()
