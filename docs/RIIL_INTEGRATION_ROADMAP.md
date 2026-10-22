# Riil + Fin Engine: first-party signals and independent source intelligence

**Architecture decision:** 22 October 2026. This supersedes the earlier
Riil-public-market-snapshot import proposal.
**Products:** `abagusdp/riil` and `kevinkent1505/fin-engine`.
**Status:** roadmap and integration design. No first-party Riil records
have been transferred to Fin Engine by this work.

## 1. Fundamental source-of-truth rule

> Fin Engine gets independently obtainable financial data from the original
> authoritative, licensed or otherwise authorized source. Riil supplies
> **first-party data that only its own product can originate or legitimately
> collect**, subject to defined purpose, transparency, authorization, privacy
> and data-sharing controls.

| Category | Where Fin Engine obtains it | Exchange from Riil? |
| --- | --- | --- |
| BI-Rate, BI JISDOR, BPS inflation, official prices and market statistics | Directly from BI, BPS or original permitted provider | **No**. Avoid copying `data/market-rates.json` and `data/market-snapshot.json`. |
| NJKB, government auction references, vehicle stocks | Government publications / permitted source adapters | **No**. Continue existing native Fin Engine pipelines. |
| Marketplace listing observations | Authorized primary marketplace feeds/crawls | **No** Riil intermediary. Respect source terms and differences between asking, reference and transaction value. |
| Riil page use / feature interaction counts | Riil's own first-party events | **Yes**, if scope and transfer are approved. Prefer aggregated counts. |
| Riil calculator scenarios, completed inputs/results, saved-plan behavior | First-party Riil product activity | **Potentially**, with much stronger safeguards; do not copy D1 raw rows by default. |
| Feedback, free text, emails, account records or identifiable saved calculations | Riil only | **Excluded by default**; any exception requires a separate narrowly defined purpose and explicit approval. |
| Financial market insights, derived indicators, B2B analytical reports | Computed by Fin Engine | Fin Engine may **optionally** publish output back to Riil via Riil-owned adapter in later phases. |

A Riil calculator submission is a **hypothetical user-entered scenario**. It
does not prove the user owns a vehicle, has a debt, took a loan, qualifies for
credit, made a purchase, or completed a transaction. Model, aggregate and
present the records accordingly. Never turn calculator usage into verified
consumer financial facts or individualized credit scoring.

## 2. Independent products and strict ownership

**Riil:** consumer interface, client-side calculations, content/CMS/editorial
policy, Cloudflare Pages/Functions/D1, tracking collection and first-party
notice/consent. Riil decides *whether, what and for what purpose* a first-party
signal may be exported.

**Fin Engine:** independent authorized public-data ingestion, quality checks,
Neon/Postgres data management, analyses, generic APIs, modular economic/
automotive domains, business dashboard and B2B data products. It processes
Riil signals only through an explicitly approved, optional inbound contract.

- Two repos, two release tracks, separate databases and credentials.
- No shared source-code imports, Git submodules or remote DB connections.
- No Riil reliance on Fin Engine availability for rendering calculators,
  recording events, publishing articles or serving the website.
- No Fin Engine reliance on Riil for NJKB, official macro data, dashboards or
  other independent financial-intelligence functionality.
- Any interface can be disabled, versioned or independently redeployed.
- The integration boundary consists of two independently maintained adapters;
  do not create a centralized integration microservice until additional consumers
  or operations justify it.

## 3. Data movement in Phase 1 and later

```text
                     INDEPENDENT EXTERNAL SOURCES
                    BI / BPS / OJK / approved market feeds
                                      |
                                source adapters
                                      |
                                      v
 RIIL PRODUCT                    FIN ENGINE PRODUCT
 ┌─────────────────────┐          ┌─────────────────────────────┐
 │ calculators, events │          │ official source history     │
 │ privacy and consent │          │ financial analytics         │
 │ Cloudflare D1       │          │ vehicle & macro domains     │
 └──────────┬──────────┘          │ Neon + Fastify + dashboard  │
            │                     └───────────────┬─────────────┘
    [outbound adapter]                            │
     purpose filter, data                          │ future optional
     minimization, aggregation                     │ data products
            │                                      v
    [versioned secure feed]             [Fin Engine published API]
            │                                      │
            ▼                                      ▼
    [Fin Engine inbound adapter]          [Riil inbound adapter]
       verify, validate, dedupe              map, cache, validate
            │                                      │
            v                                      v
    separate first-party tables            Riil's existing snapshots
    & authorized analysis                  and calculator UI
```

The reverse integration **does not start in Phase 1**. Fin Engine later
provides selected verified financial indicators or qualified vehicle context
through a product-neutral API; Riil's inbound adapter maps and caches those
results, retaining its current snapshot as fallback. It is opt-in, not a
mandatory runtime or build dependency.

## 4. Riil's existing first-party data and the constraints we observed

Riil already uses:
- `functions/api/insights/event.js` and `functions/_lib/insights.js` for daily
  aggregate event and visit counters.
- `functions/api/insights/calc.js` to store finished calculator **input and
  result data** in `insight_calcs` rows (day, page, tool, completion signal,
  language and a JSON payload).
- `functions/api/account/*` for account and saved-calculation functionality.

Important: Riil's published `privasi.html` says the usage records are used
to understand and improve Riil and create summaries without exposing individual
numbers; it explicitly promises not to sell data or give it to banks/lenders/
third parties for sales outreach. Transfers to a separately operated Fin
Engine system or B2B commercial outputs may fall outside the existing disclosed
purpose. **No such transfer is authorized simply because Riil already stores
the data.** Determine controller/processor roles, the purpose and lawful basis,
required notice/consent, permitted analytics outputs and source obligations
before implementing a production exporter.

Even when a row has no email or cookie, uncommon combinations of financial
amounts, free text or sparse segments can make it identifiable. A no-name record
is not automatically anonymous. Deleting accounts in Riil will not magically
delete copied records in Fin Engine; avoid creating such an unmanageable copy.

## 5. Fin Engine's first-party signal integration contracts

Treat the following as two **separate datasets with separate data policies**:

### 5.1 Dataset A: daily aggregated interactions (first to implement)

**Purpose:** privacy-minimized product and demand insights. Riil derives daily
counts inside its own boundary and exports only sufficiently supported cohorts.
Fin Engine consumes and analyzes counts rather than duplicating the raw event
store. No individual rows, IP hashes, cookies, account IDs or free text.

Proposed schema `riil.usage_aggregate.v1`:

```json
{
  "schema_version": "1.0",
  "dataset": "riil.usage_aggregate",
  "origin": "riil",
  "period": "2026-10-21",
  "cohort": {
    "page": "vehicle",
    "event": "calculation_completed",
    "language": "all"
  },
  "count": 123,
  "minimum_cohort_count": 20,
  "suppression_applied": true
}
```

This payload is **illustrative**, not a read of production Riil analytics.
Each exported record must meet an approved privacy threshold and combination
policy; combining independently exportable aggregates must not reveal a
suppressed segment. Avoid exposing row-level records to the public B2B API.

### 5.2 Dataset B: calculator scenario records (later, only if approved)

**Purpose:** analyze patterns that daily counts cannot represent, such as
distribution of stated terms, interest conventions, instalments or fee effects.
These are user-entered **scenarios**, not verified financial outcomes.

Preferred design: derive bounded numerical features and coarsened ranges at
the Riil boundary, and transmit only the minimum needed for approved analysis.
For example a vehicle-loan scenario could contain `tool=vehicle`,
`loan_amount_band`, `tenor_months_band`, `quoted_rate_type`,
`effective_rate_band` and `calculation_day`. Use dimension-specific
allowlists; never a generic catch-all `data` object.

Some use cases may genuinely need more precise calculation inputs. Those
require a documented necessity assessment, legal basis/consent as appropriate,
strict access controls, encryption, shorter retention, disclosure, correction
and deletion handling, and explicit contractual limits. Treat such rows as
potentially personal data. Do **not** automatically copy `insight_calcs.data`,
saved plans, salary/debt combinations, identifiers, contact details or free
text into Fin Engine/Neon.

### 5.3 Data typing and provenance

Every imported source/feature must preserve:
- `origin_product`, producer version and original tracking definition;
- collection period, cohort definition, transformation and suppression version;
- approval/purpose ID, provenance and permitted uses;
- distinction between hypothetical inputs, usage metrics, reported facts and
  confirmed transactions;
- ingestion timestamp, idempotency key, source batch ID and quality flags.

The public data domain and first-party behavior domain remain **physically
and logically separate** inside Fin Engine. Do not blend behavioral data into
`market_indicator_observations` or `vehicle_observations`.

## 6. Transfer and operational guarantees

Preferred handoff: scheduled **Riil-owned server-side exporter** creates
purpose-limited signed/versioned batch (or private authenticated API). A
**Fin Engine-owned import job** pulls the approved export into its own
staging and validation pipeline. A public browser must never call Fin Engine
with personal calculator inputs directly.

- No direct D1-to-Neon access. No shared access to production secrets.
- Source authorization and scope-checked credentials; avoid exposing them in
  URLs, client-side bundles, GitHub Actions logs, or published JSON.
- Schema validation, idempotency (`source_batch_id` + content hash), replay
  safety, input allowlists, source verification, rate limits and batch size.
- Reject unauthorized/unknown fields and quarantine invalid batches without
  persisting them.
- Data classification, encryption in transit and at rest, least-privilege
  access, documented retention and deletion/rectification procedures.
- Freshness, lag, failure and reconciliation monitoring. Failed feeds preserve
  the last valid state; Riil remains operational regardless of export status.
- Feature flag defaults `OFF` in both products until approved; independent
  CI must pass with the integration disabled.

## 7. Reconciled delivery gates

| Gate | Riil | Fin Engine | Gate to advance |
| --- | --- | --- | --- |
| **0: Baseline** | Existing Cloudflare release and golden calculator tests | Existing Python/TypeScript CI, BPS/NJKB integrity, Neon migrations | Each product builds, runs and deploys independently |
| **1: First-party interface specification** | Verify current event dictionary, privacy notice and permitted data purposes | Define usage-aggregate data contract, validation and domain-owned tests | No live transmission; explicit sharing policy |
| **2: First-party aggregate POC** | After approval, add separate server-side aggregate exporter, version and suppression checks | Add inbound adapter, separate behavioral aggregate storage and local/offline testing | An approved batch replays idempotently, no row-level leakage |
| **3: Independently sourced market data** | Keep existing market-data workflow and calculators | Add native BI-Rate / JISDOR / BPS inflation source adapters and history; continue vehicle data | Fin Engine needs no Riil market feed and reports true source provenance |
| **4: Optional scenario analytics** | Define separate notice/authorization and minimum scenario fields if needed | Build limited scenario-feature processing only after policy/data-protection gate | Traceable purpose, appropriate controls and no raw D1 dumping |
| **5: Optional return feed** | Add Riil-owned adapter, cache, editorial checks and fallback | Serve product-neutral verified indicators/B2B analytics | Riil operates if FE API is unavailable; no silent calculation drift |
| **6: Product scaling** | Continue consumer UX/education, independent CMS and growth experiments | Independent B2B APIs, dashboards, multi-domain analytics and deployment | Independent customers and releases; scale services when necessary |

Gates 1–3 can be developed in parallel without coupling the products'
deployment calendars. Gate 4 is not a prerequisite for Fin Engine's growth.

## 8. Immediate technical work in Fin Engine

1. **Retire Riil public-market importer:** remove `import:riil-market`,
   associated partner-public-market parser, schema and tests. Riil is *not*
   the canonical external macro-data provider. No live import was activated
   by the previous work.
2. **Keep generic indicator model for native sources:** Alembic revision
   `0003_market_indicators.py` creates a general market-indicator table for
   future official-source ingestion. Do not use it for first-party
   behavior data. Keep the migration number stable for installations that may
   have already applied it.
3. **Specify first-party adapter:** separately versioned usage-aggregate and
   scenario-feature contracts; fail-closed validation, no source-network
   dependency, mock datasets with no real Riil usage records.
4. **Document privacy/product gate:** decide what can be exported, why, who
   controls it, how long it is retained and which reports are permitted
   before any Riil exporter is activated.
5. **Independently build native macro ingestion** alongside the existing
   automotive source pipeline, using primary sources directly.
6. **Return adapter only later** with Riil owner approval and last-known-good
   behavior; never require Riil to wait for Fin Engine.

**Repository-change rule:** This documentation and any next-generation
first-party contract live in Fin Engine. Do not change `abagusdp/riil` or
transfer any user/usage data without a separately approved Riil-side change.
