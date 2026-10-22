# First-party Riil signals: boundary and development status

**Status:** schema-only prototype. Disabled. No real Riil activity,
calculator input, account information or usage record has been transferred.

This integration deliberately exists **only** for observations Fin Engine
cannot independently obtain from public or other authorized sources.
Fin Engine's official BI-Rate, BPS, NJKB, JISDOR and other market-source
ingestion must connect to the **original** provider instead.

## Data classes

| Class | Origin | Current decision | Storage |
| --- | --- | --- | --- |
| Aggregate usage counts | Riil's daily D1 event counters | Preferred first-party MVP after approval | Separate, proposed `behavioral_aggregates` schema |
| Banded calculator-scenario features | Riil's finalized calculator interactions | Design only, no transfer until data governance/notice/authorization | Separate, proposed `scenario_features` schema |
| Raw `insight_calcs.data` | Riil D1 | **Do not mirror** | None |
| Emails, user accounts, saved account calculations | Riil D1 | **Out of scope** | None |
| Public market data already available at BI/BPS/OJK/other sources | Original providers | **Do not import via Riil** | Independent official source tables |

Calculations are **user-entered scenarios, not transactions, loan approvals,
verified financial commitments, incomes or spending**. Product analysis must
not overstate what can be inferred from them. Banded features can still be
re-identifiable when rare; this contract is not evidence of anonymization.

## Proposed contracts implemented

`apps/analysis/riil_analysis/integrations/riil_first_party_contracts.py`

- `RiilUsageAggregateBatch` and `RiilUsageAggregate`: daily event/page
  counts, only recognized Riil event and page codes, `count >= 20`,
  no duplicate cohorts and no other fields.
- `RiilScenarioFeatureBatch` and `RiilScenarioFeature`: prototype coarse
  amount/tenor/rate bands for permitted use cases. No fine-grained salary,
  debt, input JSON, individual identifier, free-text field or session key.
- Both use Pydantic strict field allowlists and a versioned purpose reference.
  **A purpose reference in JSON does not prove lawful authorization**.

Tests in `apps/analysis/tests/test_riil_first_party_contracts.py` use
invented examples. `yarn test:analysis` runs these checks.

There is intentionally **no CLI import command, exporter, production
endpoint, scheduled job or database persistence** for first-party signals.
Do not wire one directly to Riil's D1 without separate approval.

## Future transfer design

1. Riil independently reviews the precise proposed field set against
   `privasi.html`, internal purposes, applicable data-protection requirements,
   permissible recipients/commercial usage, retention and data-subject controls.
2. Riil creates a separately deployed server-side outbound adapter: export
   permitted daily cohorts from D1 after aggregation, suppression and
   security checks. Never send private data via public static JSON or a
   browser-to-Fin-Engine call.
3. Fin Engine owns an independently deployable inbound worker that verifies
   a scoped credential or signature, purpose policy, schema, batch ID,
   deduplication key and data quality. Persist into segregated first-party
   tables only after approval; no join keys to account tables by default.
4. Test retries, outage behavior, stale data, duplicate deliveries, small
   counts, privacy deletion/retention, and domain-disable switches. Neither
   application's health or deployment may depend on the other.
5. Only if necessary, evaluate a separate, more tightly governed feature
   set from completed calculator scenarios. Raw records are not the default
   and B2B redistribution requires a distinct decision.

## Deployment and rollback

- Both repos must always pass their own CI, load their own UI and run their
  own data pipelines **with the integration disabled**.
- Riil remains the owner of first-party collection, outbound schema,
  disclosure and export timing.
- Fin Engine remains the owner of independent official data providers,
  inbound validation, analytics and its own clients.
- A failing exporter must not block Riil page requests or builds. A failing
  Riil feed must not block Fin Engine ingestion or its existing B2B API.
- A future Fin Engine-to-Riil return feed remains an **optional, separate
  adapter**, with versioned contracts and Riil-controlled last-known-good
  cache and editorial acceptance.

See [reconciled integration roadmap](./RIIL_INTEGRATION_ROADMAP.md).
