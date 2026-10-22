from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from riil_analysis.database.models import Base, DataSource, IngestionRun
from riil_analysis.refresh import public_refresh_policies, refresh_public_data


NOW = datetime(2026, 10, 22, 8, 0, tzinfo=UTC)


def prepared_database(tmp_path):
    url = f"sqlite+pysqlite:///{tmp_path / 'refresh.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    return url


def seed_completed_run(url, source, when):
    engine = create_engine(url)
    with Session(engine) as session:
        if session.get(DataSource, source) is None:
            session.add(
                DataSource(
                    source_key=source,
                    source_url="https://example.test/public",
                    created_at=when,
                )
            )
        session.add(
            IngestionRun(
                id=f"run-{source}-{int(when.timestamp())}",
                source_key=source,
                started_at=when,
                completed_at=when,
                status="completed",
                authorization_reference=None,
                requested_limit=None,
                request_delay_seconds=None,
                quality={},
                audit={},
            )
        )
        session.commit()
    engine.dispose()


def test_refresh_skips_fresh_sources(tmp_path):
    url = prepared_database(tmp_path)
    for policy in public_refresh_policies():
        seed_completed_run(url, policy.source_id, NOW - timedelta(days=1))

    called = []
    result = refresh_public_data(
        url, now=NOW, ingest_source=lambda **kwargs: called.append(kwargs) or 0
    )
    assert result["status"] == "ok"
    assert called == []
    assert {entry["status"] for entry in result["sources"]} == {"fresh"}


def test_refresh_only_due_sources_and_force_overrides(tmp_path):
    url = prepared_database(tmp_path)
    policies = public_refresh_policies()
    seed_completed_run(url, policies[0].source_id, NOW - timedelta(days=1))
    seed_completed_run(url, policies[1].source_id, NOW - timedelta(days=45))
    seed_completed_run(url, policies[2].source_id, NOW - timedelta(days=1))

    calls = []

    def ingest(**kwargs):
        calls.append(kwargs["source_id"])
        assert kwargs["persist_db"] is True
        assert kwargs["authorization_ref"] is None
        return 0

    result = refresh_public_data(url, now=NOW, ingest_source=ingest)
    assert result["status"] == "ok"
    assert calls == [policies[1].source_id]

    calls.clear()
    forced = refresh_public_data(url, now=NOW, force=True, ingest_source=ingest)
    assert forced["status"] == "ok"
    assert calls == [policy.source_id for policy in policies]


def test_failed_refresh_is_reported_but_other_sources_continue(tmp_path):
    url = prepared_database(tmp_path)
    calls = []

    def ingest(**kwargs):
        calls.append(kwargs["source_id"])
        if len(calls) == 1:
            raise ValueError("source temporarily unavailable")
        return 0

    result = refresh_public_data(url, now=NOW, ingest_source=ingest)
    assert result["status"] == "partial_failure"
    assert len(calls) == len(public_refresh_policies())
    assert result["sources"][0]["status"] == "failed"
    assert result["sources"][1]["status"] == "updated"
    assert "source temporarily unavailable" in result["sources"][0]["error"]


def test_freshness_uses_latest_success_only(tmp_path):
    url = prepared_database(tmp_path)
    policy = public_refresh_policies()[0]
    seed_completed_run(url, policy.source_id, NOW - timedelta(days=120))
    seed_completed_run(url, policy.source_id, NOW - timedelta(days=2))
    calls = []
    result = refresh_public_data(
        url, now=NOW, ingest_source=lambda **kwargs: calls.append(kwargs) or 0
    )
    assert result["sources"][0]["status"] == "fresh"
    assert policy.source_id not in [c["source_id"] for c in calls]
