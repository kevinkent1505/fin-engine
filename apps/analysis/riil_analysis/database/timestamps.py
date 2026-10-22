"""Database timestamp handling shared by ingestion persistence.

SQLite drops timezone information when reading DateTime(timezone=True) values.
Fin Engine always writes UTC, so naive values read from SQLite are UTC.
PostgreSQL preserves timezone-aware values.
"""

from datetime import UTC, datetime


def as_utc(value: datetime) -> datetime:
    """Return an aware UTC timestamp, interpreting database-naive values as UTC."""
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
