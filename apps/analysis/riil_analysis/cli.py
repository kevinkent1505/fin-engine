import argparse
import csv
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from riil_analysis.database.config import get_database_url
from riil_analysis.database.persistence import (
    persist_ingestion,
    persist_regional_vehicle_statistics,
)
from riil_analysis.ingestion.models import (
    CanonicalVehicleObservation,
    IngestionAudit,
    IngestionQualityReport,
)
from riil_analysis.ingestion.pipeline import normalize_records
from riil_analysis.regional import RegionalVehicleStatisticInput
from riil_analysis.scrapers.registry import (
    ALL_SOURCE_IDS,
    REGIONAL_SOURCE_FACTORIES,
    get_regional_source_adapter,
    get_source_adapter,
)


CSV_FIELDS = [
    "source",
    "source_record_id",
    "source_url",
    "observed_at",
    "make",
    "model",
    "variant",
    "type_name",
    "year",
    "region",
    "price",
    "price_kind",
    "currency",
    "category",
    "njkb",
    "weight_factor",
    "dp_pkb",
    "dp_pkb_expected",
    "dp_pkb_difference",
    "dp_pkb_check",
    "metadata",
]

REGIONAL_CSV_FIELDS = [
    "source",
    "source_url",
    "observed_at",
    "year",
    "region",
    "passenger_cars",
    "buses",
    "trucks",
    "motorcycles",
    "total",
    "metadata",
]


def observation_row(
    observation: CanonicalVehicleObservation,
) -> dict[str, Any]:
    data = observation.model_dump(mode="json")
    data["metadata"] = json.dumps(
        data["metadata"],
        ensure_ascii=False,
        sort_keys=True,
    )
    return data


def write_csv(
    observations: list[CanonicalVehicleObservation],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=CSV_FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        for observation in observations:
            writer.writerow(observation_row(observation))


def write_regional_csv(
    observations: list[RegionalVehicleStatisticInput],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=REGIONAL_CSV_FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        for observation in observations:
            data = observation.model_dump(mode="json")
            data["metadata"] = json.dumps(
                data["metadata"],
                ensure_ascii=False,
                sort_keys=True,
            )
            writer.writerow(data)


def write_audit(
    output_path: Path,
    *,
    report: IngestionQualityReport,
    audit: IngestionAudit,
) -> Path:
    audit_path = output_path.with_suffix(".audit.json")
    audit_path.write_text(
        json.dumps(
            {
                "quality": report.model_dump(),
                "audit": audit.model_dump(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return audit_path


def ingest_regional(
    source_id: str,
    output_path: Path | None,
    limit: int | None,
    persist_db: bool,
) -> int:
    started_at = datetime.now(UTC)
    adapter = get_regional_source_adapter(source_id)
    observations = adapter.run()
    if limit is not None:
        observations = observations[:limit]

    output_value: str | None = None
    if output_path is not None:
        write_regional_csv(observations, output_path)
        output_value = str(output_path)

    database_result: dict[str, int | str] | None = None
    if persist_db:
        database_result = persist_regional_vehicle_statistics(
            database_url=get_database_url(),
            source_key=adapter.source_id,
            source_url=adapter.source_url,
            observations=observations,
            started_at=started_at,
            requested_limit=limit,
        )

    quality = {
        "source": adapter.source_id,
        "total_records": len(observations),
        "valid_records": len(observations),
        "invalid_records": 0,
        "dataset_type": "regional_vehicle_statistics",
    }
    print(
        json.dumps(
            {
                "output": output_value,
                "audit_output": None,
                "database": database_result,
                "quality": quality,
            },
            indent=2,
        )
    )
    return 0 if observations else 1


def ingest(
    source_id: str,
    output_path: Path | None,
    limit: int | None,
    input_file: Path | None,
    authorization_ref: str | None,
    start_url: str | None,
    request_delay_seconds: float,
    persist_db: bool,
) -> int:
    if source_id in REGIONAL_SOURCE_FACTORIES:
        return ingest_regional(
            source_id=source_id,
            output_path=output_path,
            limit=limit,
            persist_db=persist_db,
        )

    started_at = datetime.now(UTC)

    adapter = get_source_adapter(source_id)
    adapter.set_fetch_limit(limit)
    adapter.set_input_path(input_file)
    adapter.set_authorization_reference(authorization_ref)
    adapter.set_start_url(start_url)
    adapter.set_request_delay_seconds(request_delay_seconds)

    raw_records = adapter.run()

    if limit is not None:
        raw_records = raw_records[:limit]

    observations, report, audit = normalize_records(
        raw_records,
        source=adapter.source_id,
    )

    output_value: str | None = None
    audit_output_value: str | None = None

    if output_path is not None:
        write_csv(observations, output_path)
        audit_path = write_audit(
            output_path,
            report=report,
            audit=audit,
        )
        output_value = str(output_path)
        audit_output_value = str(audit_path)

    database_result: dict[str, int | str] | None = None
    if persist_db:
        database_result = persist_ingestion(
            database_url=get_database_url(),
            source_key=adapter.source_id,
            source_url=adapter.source_url,
            observations=observations,
            report=report,
            audit=audit,
            started_at=started_at,
            authorization_reference=authorization_ref,
            requested_limit=limit,
            request_delay_seconds=request_delay_seconds,
        )

    print(
        json.dumps(
            {
                "output": output_value,
                "audit_output": audit_output_value,
                "database": database_result,
                "quality": report.model_dump(),
            },
            indent=2,
        )
    )

    return 0 if observations else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fin-engine-data",
        description="Fin Engine external data ingestion tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Fetch, normalize and persist/export an external source.",
    )
    ingest_parser.add_argument(
        "--source",
        required=True,
        choices=ALL_SOURCE_IDS,
    )
    ingest_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional CSV output path. Cloud jobs may omit this when "
            "--persist-db is enabled."
        ),
    )
    ingest_parser.add_argument(
        "--persist-db",
        action="store_true",
        help="Persist the normalized source snapshot to DATABASE_URL.",
    )
    ingest_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Optional record/detail-page limit. Authorized live crawlers "
            "default to 10 and enforce a hard maximum of 50 per run."
        ),
    )
    ingest_parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Local source file for file-backed or authorized-feed adapters.",
    )
    ingest_parser.add_argument(
        "--authorization-ref",
        default=None,
        help=(
            "Permission, contract, ticket, API/feed agreement, or other "
            "authorization reference for restricted-source data access."
        ),
    )
    ingest_parser.add_argument(
        "--start-url",
        default=None,
        help=(
            "Optional authorized marketplace search/listing URL. The adapter "
            "rejects URLs outside its own host."
        ),
    )
    ingest_parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=2.0,
        help=(
            "Minimum delay between outbound requests. Must be >= 1.0; "
            "default is 2.0 seconds."
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        if args.output is None and not args.persist_db:
            parser.error("ingest requires --output and/or --persist-db")

        return ingest(
            source_id=args.source,
            output_path=args.output,
            limit=args.limit,
            input_file=args.input_file,
            authorization_ref=args.authorization_ref,
            start_url=args.start_url,
            request_delay_seconds=args.request_delay_seconds,
            persist_db=args.persist_db,
        )

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
