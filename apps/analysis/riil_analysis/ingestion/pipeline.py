from collections.abc import Iterable

from pydantic import ValidationError

from riil_analysis.ingestion.models import (
    CanonicalVehicleObservation,
    IngestionAudit,
    IngestionQualityReport,
    RawVehicleObservation,
    RejectedRecord,
)
from riil_analysis.normalization.vehicle import (
    normalize_vehicle_observation,
)


def normalize_records(
    records: Iterable[RawVehicleObservation],
    *,
    source: str,
) -> tuple[
    list[CanonicalVehicleObservation],
    IngestionQualityReport,
    IngestionAudit,
]:
    output: list[CanonicalVehicleObservation] = []
    report = IngestionQualityReport(source=source)
    audit = IngestionAudit()
    seen: set[tuple[str, str]] = set()

    for raw in records:
        report.total_records += 1

        dedupe_key = (raw.source, raw.source_record_id)
        if dedupe_key in seen:
            report.duplicate_records += 1
            audit.duplicate_record_ids.append(raw.source_record_id)
            continue
        seen.add(dedupe_key)

        if raw.price_raw in (None, ""):
            report.missing_price_records += 1
            report.invalid_records += 1
            audit.rejected_records.append(
                RejectedRecord(
                    source_record_id=raw.source_record_id,
                    reason="missing_price",
                )
            )
            continue

        try:
            normalized = normalize_vehicle_observation(raw)
        except (ValueError, ValidationError) as error:
            message = str(error)
            if "year" in message.lower():
                report.invalid_year_records += 1
            report.normalization_failures += 1
            report.invalid_records += 1
            audit.rejected_records.append(
                RejectedRecord(
                    source_record_id=raw.source_record_id,
                    reason=f"normalization_failure: {message}",
                )
            )
            continue

        # The current semantic relationship check is NJKB-specific.
        # Other price kinds should not be counted as skipped NJKB checks.
        if normalized.price_kind == "njkb":
            if normalized.dp_pkb_check == "not_available":
                report.semantic_checks_skipped += 1
            else:
                report.semantic_checks_total += 1
                if normalized.dp_pkb_check == "pass":
                    report.semantic_checks_passed += 1
                else:
                    report.semantic_checks_failed += 1
                    audit.semantic_failure_record_ids.append(
                        normalized.source_record_id
                    )

        output.append(normalized)
        report.valid_records += 1

    return output, report, audit
