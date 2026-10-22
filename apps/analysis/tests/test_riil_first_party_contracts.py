"""Only synthetic data: none of Riil's real first-party records are used."""
import copy
from datetime import date
from uuid import UUID

import pytest
from pydantic import ValidationError

from riil_analysis.integrations.riil_first_party_contracts import (
    RiilScenarioFeatureBatch, RiilUsageAggregateBatch,
)


def _usage_batch():
    return {
        "schema_version": "1.0",
        "dataset": "riil.usage_aggregate",
        "producer": "riil",
        "source_batch_id": "b79c540d-cb0c-4020-a877-bb2861369323",
        "purpose_reference": "approved-purpose-reference",
        "aggregation_policy_version": "1",
        "minimum_cohort_count": 20,
        "records": [{
            "day": "2026-10-21",
            "event": "calculation_completed",
            "page": "vehicle",
            "count": 40,
        }],
    }


def _scenario_batch():
    return {
        "schema_version": "1.0",
        "dataset": "riil.scenario_features",
        "producer": "riil",
        "source_batch_id": "d3db81d0-0fb4-4da8-a254-63024349db67",
        "purpose_reference": "approved-purpose-reference",
        "feature_policy_version": "1",
        "records": [{
            "calculation_day": "2026-10-21",
            "tool": "vehicle",
            "amount_band": "25m_to_100m",
            "term_months_band": "36_to_59",
            "quoted_rate_type": "flat",
            "effective_rate_band": "15_to_30",
        }],
    }


def test_usage_aggregate_contract_accepts_approved_shape() -> None:
    model = RiilUsageAggregateBatch.model_validate(_usage_batch())
    assert model.records[0].count == 40
    assert model.records[0].day == date(2026, 10, 21)
    assert model.source_batch_id == UUID("b79c540d-cb0c-4020-a877-bb2861369323")


@pytest.mark.parametrize("field,value", [
    ("count", 19), ("count", -1), ("count", 20.1),
    ("page", "unknown-route"), ("event", "unknown_event"),
    ("day", "2099-01-01"),
])
def test_usage_aggregate_fails_closed_on_invalid_cohorts(field, value) -> None:
    batch = _usage_batch()
    batch["records"][0][field] = value
    with pytest.raises(ValidationError):
        RiilUsageAggregateBatch.model_validate(batch)


def test_usage_aggregate_rejects_raw_data_and_individual_identifiers() -> None:
    batch = _usage_batch()
    batch["records"][0]["data"] = {"salary": 10_000_000}
    with pytest.raises(ValidationError):
        RiilUsageAggregateBatch.model_validate(batch)

    batch = _usage_batch()
    batch["records"][0]["email"] = "someone@example.invalid"
    with pytest.raises(ValidationError):
        RiilUsageAggregateBatch.model_validate(batch)

    batch = _usage_batch()
    batch["account_id"] = "abc"
    with pytest.raises(ValidationError):
        RiilUsageAggregateBatch.model_validate(batch)


def test_usage_batch_rejects_duplicate_cohorts_and_fake_versions() -> None:
    batch = _usage_batch()
    batch["records"].append(copy.deepcopy(batch["records"][0]))
    with pytest.raises(ValidationError, match="Duplicate aggregate cohort"):
        RiilUsageAggregateBatch.model_validate(batch)

    batch = _usage_batch()
    batch["schema_version"] = "2.0"
    with pytest.raises(ValidationError):
        RiilUsageAggregateBatch.model_validate(batch)


def test_scenario_contract_only_allows_predefined_coarse_features() -> None:
    model = RiilScenarioFeatureBatch.model_validate(_scenario_batch())
    assert model.records[0].tool == "vehicle"
    assert model.records[0].amount_band == "25m_to_100m"

    batch = _scenario_batch()
    batch["records"][0]["raw_input"] = {"salary": 20_000_000}
    with pytest.raises(ValidationError):
        RiilScenarioFeatureBatch.model_validate(batch)

    batch = _scenario_batch()
    batch["records"][0]["amount_band"] = 21_500_000
    with pytest.raises(ValidationError):
        RiilScenarioFeatureBatch.model_validate(batch)

    batch = _scenario_batch()
    batch["records"][0]["user_id"] = "persistent-tracking-token"
    with pytest.raises(ValidationError):
        RiilScenarioFeatureBatch.model_validate(batch)
