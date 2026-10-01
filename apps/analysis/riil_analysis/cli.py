import argparse
import csv
import json
from pathlib import Path
from typing import Any

from riil_analysis.ingestion.models import CanonicalVehicleObservation
from riil_analysis.ingestion.pipeline import normalize_records
from riil_analysis.scrapers.registry import (
    SOURCE_FACTORIES,
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


def ingest(source_id: str, output_path: Path, limit: int | None) -> int:
    adapter = get_source_adapter(source_id)
    raw_records = adapter.run()

    if limit is not None:
        raw_records = raw_records[:limit]

    observations, report = normalize_records(
        raw_records,
        source=adapter.source_id,
    )
    write_csv(observations, output_path)

    print(
        json.dumps(
            {
                "output": str(output_path),
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
        help="Fetch, parse, normalize and export a vehicle source.",
    )
    ingest_parser.add_argument(
        "--source",
        required=True,
        choices=sorted(SOURCE_FACTORIES),
    )
    ingest_parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )
    ingest_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional development limit applied after parsing.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        return ingest(
            source_id=args.source,
            output_path=args.output,
            limit=args.limit,
        )

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
