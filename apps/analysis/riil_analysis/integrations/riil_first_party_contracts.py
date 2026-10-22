"""Validation-only contracts for possible Riil first-party data transfers.

NO network fetch, data-store writes, automatic export, or implicit permission
to ingest customer data. The Riil controller must approve an exact purpose and
source-side transformation before any real batch is supplied.
"""
from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

MIN_PUBLIC_AGGREGATE_COUNT = 20

EVENTS = Literal[
    "page_view", "calculation_completed", "result_shared", "goal_shared",
    "save_opened", "challenge_created", "quiz_finished",
]
PAGES = Literal[
    "home", "vehicle", "mortgage", "card", "paylater", "compare", "payoff",
    "goal", "debt", "quiz", "about", "method", "privacy", "article", "articles",
    "buy", "money", "account", "notfound", "other", "rate", "promo", "trend",
    "buffer", "dampak", "loan", "dampak-kurs", "dampak-bbm",
    "dampak-inflasi", "dampak-emas", "dampak-ihsg",
]
TOOLS = Literal[
    "brochure", "paylater", "vehicle", "mortgage", "card",
    "payoff", "compare", "goal", "debt",
]

# Input bands are coarse *proposed* values; they are not ready to share until
# sparse-cohort/re-identification and Riil's privacy-policy requirements pass.
VALUE_BANDS = Literal[
    "under_5m", "5m_to_25m", "25m_to_100m", "100m_to_500m",
    "500m_to_2b", "over_2b", "not_provided",
]
TERM_BANDS = Literal[
    "under_12", "12_to_35", "36_to_59", "60_to_119",
    "120_to_239", "240_plus", "not_provided",
]


class RiilUsageAggregate(BaseModel):
    """One supported day/event/tool count, not an individual interaction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    day: date
    event: EVENTS
    page: PAGES
    count: int = Field(ge=MIN_PUBLIC_AGGREGATE_COUNT)

    @model_validator(mode="after")
    def check_date(self):
        if self.day > datetime.now(UTC).date():
            raise ValueError("Aggregate day cannot be in the future.")
        return self


class RiilUsageAggregateBatch(BaseModel):
    """Proposed first-party aggregate handoff, still disabled in production."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    dataset: Literal["riil.usage_aggregate"]
    producer: Literal["riil"]
    source_batch_id: UUID
    purpose_reference: str = Field(min_length=8, max_length=128)
    aggregation_policy_version: str = Field(min_length=1, max_length=64)
    minimum_cohort_count: Literal[20] = 20
    records: list[RiilUsageAggregate] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def check_unique(self):
        keys = [(item.day, item.event, item.page) for item in self.records]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate aggregate cohort in one source batch.")
        return self


class RiilScenarioFeature(BaseModel):
    """PROPOSED coarse scenario features, *not* approved for transfer.

    A scenario is a user-entered calculation, not an actual consumer loan,
    payment, verified income, financial obligation or creditworthiness record.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    calculation_day: date
    tool: TOOLS
    amount_band: VALUE_BANDS
    term_months_band: TERM_BANDS
    quoted_rate_type: Literal["flat", "effective", "unknown"]
    effective_rate_band: Literal[
        "0_to_5", "5_to_15", "15_to_30", "30_plus", "unavailable"
    ]

    @model_validator(mode="after")
    def check_day(self):
        if self.calculation_day > datetime.now(UTC).date():
            raise ValueError("Scenario day cannot be in the future.")
        return self


class RiilScenarioFeatureBatch(BaseModel):
    """Development-only future contract; exporting such rows is DISABLED.

    A purpose reference does NOT imply that source collection, notice/consent,
    re-identification checks or retention/deletion mechanisms are approved.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    dataset: Literal["riil.scenario_features"]
    producer: Literal["riil"]
    source_batch_id: UUID
    purpose_reference: str = Field(min_length=8, max_length=128)
    feature_policy_version: str = Field(min_length=1, max_length=64)
    records: list[RiilScenarioFeature] = Field(min_length=1, max_length=1000)
