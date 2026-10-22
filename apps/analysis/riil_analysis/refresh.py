"""Freshness-aware public-data refresh for analysis API and batch jobs.

Marketplace crawlers and synthetic seeds are deliberately excluded.
"""
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from typing import Any, Callable

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from riil_analysis.config import DEFAULT_MARKETPLACE_REQUEST_DELAY_SECONDS
from riil_analysis.config.sources import latest_official_source
from riil_analysis.database.config import normalize_database_url
from riil_analysis.database.models import IngestionRun
from riil_analysis.database.timestamps import as_utc

logger = logging.getLogger(__name__)

# PostgreSQL session-level advisory lock across workers and scheduled runners.
REFRESH_LOCK_ID = 748923601


@dataclass(frozen=True)
class RefreshPolicy:
    source_id: str
    max_age: timedelta


def public_refresh_policies() -> tuple[RefreshPolicy, ...]:
    """Conservative cadence; official release IDs remain year-specific."""
    return (
        RefreshPolicy(latest_official_source("njkb").source_id, timedelta(days=90)),
        RefreshPolicy(
            latest_official_source("regional_vehicle_stock").source_id,
            timedelta(days=30),
        ),
        RefreshPolicy("djp_vehicle_auction_limits", timedelta(days=7)),
    )


def _latest_completed_at(session: Session, source_id: str) -> datetime | None:
    value = session.scalar(
        select(func.max(IngestionRun.completed_at)).where(
            IngestionRun.source_key == source_id,
            IngestionRun.status == "completed",
        )
    )
    return as_utc(value) if value is not None else None


def refresh_public_data(
    database_url: str,
    *,
    force: bool = False,
    now: datetime | None = None,
    ingest_source: Callable[..., int] | None = None,
) -> dict[str, Any]:
    """Refresh due public government sources with per-source error isolation.

    Successful persisted ingestion runs determine freshness across restarts.
    A PostgreSQL advisory lock avoids concurrent fetches and writes from
    multiple analysis workers, CI jobs and manual commands.
    """
    if ingest_source is None:
        from riil_analysis.cli import ingest
        ingest_source = ingest

    checked_at = as_utc(now) if now is not None else datetime.now(UTC)
    engine = create_engine(normalize_database_url(database_url), pool_pre_ping=True)
    results: list[dict[str, str]] = []
    acquired = False

    try:
        with engine.connect() as lock_connection:
            if engine.dialect.name == "postgresql":
                acquired = bool(
                    lock_connection.scalar(
                        text("SELECT pg_try_advisory_lock(:lock_id)"),
                        {"lock_id": REFRESH_LOCK_ID},
                    )
                )
                if not acquired:
                    return {
                        "status": "busy",
                        "detail": "Another public-data refresh is already running.",
                        "sources": [],
                    }
            try:
                for policy in public_refresh_policies():
                    try:
                        with Session(engine) as session:
                            last_run = _latest_completed_at(session, policy.source_id)

                        if (
                            not force
                            and last_run is not None
                            and checked_at - last_run < policy.max_age
                        ):
                            results.append(
                                {
                                    "source": policy.source_id,
                                    "status": "fresh",
                                    "last_success": last_run.isoformat(),
                                }
                            )
                            continue

                        logger.info("Refreshing public source %s", policy.source_id)
                        exit_code = ingest_source(
                            source_id=policy.source_id,
                            output_path=None,
                            limit=25 if policy.source_id == "djp_vehicle_auction_limits" else None,
                            input_file=None,
                            authorization_ref=None,
                            start_url=None,
                            request_delay_seconds=DEFAULT_MARKETPLACE_REQUEST_DELAY_SECONDS,
                            persist_db=True,
                        )
                        if exit_code != 0:
                            raise RuntimeError(f"Ingestion returned exit code {exit_code}")

                        results.append({"source": policy.source_id, "status": "updated"})
                    except Exception as error:
                        logger.exception("Refresh failed for %s", policy.source_id)
                        results.append(
                            {
                                "source": policy.source_id,
                                "status": "failed",
                                "error": f"{type(error).__name__}: {error}",
                            }
                        )
            finally:
                if acquired:
                    lock_connection.execute(
                        text("SELECT pg_advisory_unlock(:lock_id)"),
                        {"lock_id": REFRESH_LOCK_ID},
                    )
    finally:
        engine.dispose()

    return {
        "status": (
            "partial_failure"
            if any(item["status"] == "failed" for item in results)
            else "ok"
        ),
        "checked_at": checked_at.isoformat(),
        "sources": results,
    }
