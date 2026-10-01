from collections.abc import Iterable

from pydantic import ValidationError

from riil_analysis.ingestion.models import (
    CanonicalVehicleObservation,
    IngestionQualityReport,
    RawVehicleObservation,
)
from riil_analysis.normalization.vehicle import (
    normalize_vehicle_observation,
)


def normalize_records(
    records: Iterable[RawVehicleObservation],
    *,
    source: str,
) -> tuple[list[CanonicalVehicleObservation], IngestionQualityReport]:
    output: list[CanonicalVehicleObservation] = []
    report = IngestionQualityReport(source=source)
    seen: set[tuple[str, str]] = set()

    for raw in records:
        report.total_records += 1

        dedupe_key = (raw.source, raw.source_record_id)
        if dedupe_key in seen:
            report.duplicate_records += 1
            continue
        seen.add(dedupe_key)

        if raw.price_raw in (None, ""):
            report.missing_price_records += 1
            report.invalid_records += 1
            continue

        try:
            normalized = normalize_vehicle_observation(raw)
        except (ValueError, ValidationError) as error:
            message = str(error).lower()
            if "year" in message:
                report.invalid_year_records += 1
            report.normalization_failures += 1
            report.invalid_records += 1
            continue

        output.append(normalized)
        report.valid_records += 1

    return output, report
