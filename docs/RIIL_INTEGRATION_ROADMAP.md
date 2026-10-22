# Riil + Fin Engine: independent products, phased data exchange

**Status:** updated architecture decision and proposed roadmap, 22 October 2026.
**Repositories:** `abagusdp/riil` (reviewed read-only, `main`) and `kevinkent1505/fin-engine` (`feature/marketplace-poc`).
**Non-negotiable:** both products must remain independently operable, developable, deployable, and testable. They cooperate through adapters and stable data contracts, never through shared application internals.

## 1. The direction of integration is deliberate

**Phase 1: Riil → adapter → Fin Engine.** Riil is initially a **source** of Riil-produced/curated financial signals and, once separately approved, privacy-reviewed aggregate usage insights. Fin Engine consumes an asynchronous, versioned feed. It does not control Riil's collection, publication, or consumer experience.

**Later phases: Fin Engine → adapter → Riil.** Fin Engine may publish verified financial indicators, source-backed vehicle context, and other derived signals back to Riil. The reverse feed is opt-in, versioned, and translated by an independent Riil-side adapter into Riil's existing static-data format. It is never a dependency of Riil's core calculators.

**Always:** Fin Engine also operates independently using official, licensed, or authorized external sources. Riil operates independently using its existing market-rate workflow, static snapshots, Cloudflare backend and calculator engines. A failed integration must not stop either application.

The relation is **two independent products with potentially bidirectional data exchange**, not a parent application and dependent backend.

## 2. Existing product ownership (verified against the repositories)

| Ownership | Riil | Fin Engine |
| --- | --- | --- |
| User/product experience | Consumer calculators, Dampak tools, bilingual content and articles, CMS | Business dashboard, enterprise-oriented analytical experiences |
| Core calculations | Client-side loan/IRR, savings, personal impact engines | Python analysis, vehicle reference and valuation functions |
| Storage | Cloudflare D1 for accounts/insights; Git-tracked editorial market snapshots | Neon PostgreSQL historical source records and analytical observations |
| Operational jobs | `fetch-rates.py` + `.github/workflows/rates.yml`, article and Dampak builders | Python ingestion CLI, source adapters, FastAPI analysis, Fastify public API |
| Source-specific data | `data/market-rates.json`, `data/market-snapshot.json`, Riil analytics counters | NJKB, BPS vehicle stock, DJP auction references, authorized vehicle-market adapters |
| Changes and release | Riil's repo owner and CI/CD | Fin Engine's repo owner and CI/CD |

**Do not move** Riil's calculators, auth, CMS, articles, D1 tables or `assets/riil.js` into Fin Engine. **Do not give** Fin Engine direct D1 access or Riil direct Neon access. No cross-repository imports, Git submodules, shared deployment pipeline or mandatory live calls between the products.

### Critical privacy observation

Riil's tracker currently retains some finished calculator inputs in Cloudflare D1 (`functions/_lib/insights.js`), not only event counts. Some such financial values may still be sensitive or re-identifiable even without names, emails or IP addresses. This roadmap **does not authorize** exporting those raw records to Fin Engine. Any usage-derived feed requires an explicit disclosure/lawful-basis and data-governance review, aggregation and small-cohort suppression **before** transfer, retention and deletion rules, security controls, and an approved commercial-use policy. The default is no personal or row-level calculator data transfer.

## 3. Target architecture: adapters at both boundaries

```text
Riil product (repo A)                           Fin Engine product (repo B)
┌─────────────────────────────┐                  ┌────────────────────────────────┐
│ Static calculators & tools  │                  │ Independent official sources   │
│ Articles, CMS, Cloudflare   │                  │ BI, BPS, NJKB, etc.            │
│ D1, existing market data    │                  │                                │
└──────────────┬──────────────┘                  └───────────────┬────────────────┘
               │                                                 │
      [Riil outbound adapter]                                     │
       export approved data                                       │
       versioned & asynchronous                                   │
               │                                                 │
               ▼                                                 ▼
       Transfer boundary ───────► [Fin Engine inbound adapter]  ingestion
        optional, retryable         validate, dedupe, map         │
        signed / authenticated                    │               │
                                                  ▼               ▼
                                           Fin Engine Core
                                       domains + Neon + analytics
                                                  │
                             (later only)          ▼
        [Riil inbound adapter] ◄─────── [Fin Engine published API]
        translate, validate, cache            versioned, source-backed
               │
               ▼
       Existing Riil snapshot/build
               │
               ▼
       Riil pages and browser math
```

**Adapter placement:** an adapter is a thin integration module/job, not necessarily a third microservice or third repository. For the initial scale, each owner maintains its own edge: Riil's outbound exporter in Riil, Fin Engine's importer in Fin Engine; later Fin Engine's publisher in Fin Engine and Riil's inbound adapter in Riil. If multiple external products eventually depend on the bridge, consider extracting an independently deployed integration gateway. Do not introduce that infrastructure prematurely.

**No forced uptime coupling:** scheduled exports/ingestions, durable snapshots, idempotent imports, last-known-good behavior, and explicit freshness metadata. Riil's pages still work if Fin Engine is down; Fin Engine's existing core products still work if Riil stops sending data.

## 4. Phase 1: Riil feeds Fin Engine (first integration milestone)

### 4.1 Start with two distinct *candidate* feeds

1. **Public financial market snapshot feed (safe first POC).** Riil already has `data/market-rates.json` and `data/market-snapshot.json`, with BI-Rate, available SBDK observations, JISDOR, inflation and other dated market references. Fin Engine can ingest **only allowed published fields** via a provider-specific `riil_market_snapshot_v1` adapter while preserving the **original publisher, source URL, as-of date, unit, caveat, and Riil's editorial status**. Riil is the source of the compiled artifact, not automatically the original publisher of its figures. Respect original source licensing before storing/redistributing outside Riil.
2. **Aggregate product-usage feed (optional and governance-gated).** Riil's event/calc infrastructure provides a possible source of aggregate activity signals such as daily counts per tool. This is strategically valuable to Fin Engine's later research/market-intelligence work, but no real usage data is transferred until authorization, product disclosure, data-minimization, privacy review, suppression, retention and security requirements are met. **Never send raw input values, per-session histories, rare combinations, user identifiers or account data as a shortcut.**

A read-only Fin Engine prototype may initially fetch Riil's *public* published JSON artifacts; that is a technical convenience, not shared runtime dependency. A formal Riil-owned export job/adapter should be introduced only when the first contract and ownership are approved. Do not change Riil production or its workflow during Fin Engine-only prototyping.

### 4.2 Producer/consumer contract: Riil outbound

**Proposed contract for public market data** (`riil.market_snapshot.v1`), independent of Riil's internal JSON layout:

```json
{
  "schema_version": "1.0",
  "producer": "riil",
  "dataset": "riil.market_snapshot",
  "exported_at": "YYYY-MM-DDTHH:mm:ssZ",
  "records": [
    {
      "indicator": "bi_rate",
      "value": 5.75,
      "unit": "percent_per_year",
      "as_of": "YYYY-MM-DD",
      "original_publisher": "Bank Indonesia",
      "source_url": "https://www.bi.go.id/id/statistik/indikator/BI-Rate.aspx",
      "caveat": "Policy rate; not a retail credit offer"
    }
  ]
}
```

The values above are a **contract illustration**, not a freshly verified market observation. The adapter must carry the publication's actual dates and caveats. A *separate schema* is required for any approved aggregate behavior feed: at minimum measurement window, metric name, population definition, aggregate count, applied suppression policy and export version. Never blend behavior data with public financial statistics just because both originate at Riil.

### 4.3 Transfer and operational rules

- Prefer an **asynchronous artifact/feed handoff**: Riil produces a versioned signed JSON/JSONL export or approved read-only snapshot, Fin Engine independently pulls/imports it on its own schedule. Alternatively, an authenticated push to a Fin Engine ingestion endpoint is fine **only if it runs as a retryable background job, not on the calculator or page-request critical path**.
- Riil **never needs Fin Engine to accept an export** to complete its own page build, CMS save or calculator result. Fin Engine does not need Riil for its native provider ingest or B2B API.
- Authenticate private feeds using server-side credentials/short-lived signing; no secrets in browser bundles, public JSON, build logs or commit messages. Apply scoped permissions.
- Import pipeline checks contract schema, source authorization, allowed fields, units, time semantics, counts, duplicates, checksum and idempotency key; rejects malformed or partial batches into quarantine and preserves the last valid snapshot.
- Keep Riil's identifiers internal. Fin Engine stores separate `source_key=riil_*` provenance and must distinguish curated/reported figures from independently retrieved/verified figures.
- Track feed status (last successful transfer, age, count, rejected count) separately in each product. Outages and retries must not produce duplicates or silently change an indicator's meaning.

**Phase 1 acceptance:** Fin Engine imports at least one validated Riil-origin dataset; both applications build/run/deploy independently with the connection disabled; no direct database access or user-data leakage; replaying a batch changes no results; integration failure causes no user-facing Riil outage.

## 5. Later phases: Fin Engine can feed back through an adapter

Fin Engine may increasingly become an independent provider of economic indicators and qualified market intelligence. Riil consumes **only an explicitly selected set** via a **Riil-owned inbound adapter**:

```text
Fin Engine Fastify /v1/* API (generic semantics and provenance)
    -> Riil inbound adapter (authentication, mapping, validation, editorial policy)
    -> last-known-good snapshot / feature-flagged cache
    -> Riil's existing `data/market-rates.json` or `data/market-snapshot.json` workflow
    -> Riil build-articles / build-dampak / MARKET block
    -> normal Riil static pages
```

The API remains **product-neutral**: no Riil-specific field names or UI strings in Fin Engine. The adapter translates to Riil's schemas, enforces publication/quality gates, and preserves manual editorial overrides. Data comes into Riil at build time or through a cached Cloudflare Function only when a clear feature requires dynamic access. Browser-side calculators retain their deterministic arithmetic and safe local defaults.

**Reverse-flow acceptance:** disabling the inbound adapter or losing Fin Engine connectivity leaves Riil operational with a timestamped last-known-good snapshot; Fin Engine's releases don't silently change consumer calculations; each repository's contract tests catch breaking changes.

## 6. Modular Fin Engine design

Keep the existing Python analysis + Fastify API + Next.js dashboard as an independent, modular monolith for now; introduce bounded submodules before splitting services:

```text
apps/analysis/riil_analysis/         existing modules (incrementally evolve)
  integrations/
    riil/
      import_market_snapshot.py      PROPOSED, not implemented
      import_aggregates.py           OPTIONAL after governance approval
  domains/
    automotive/                      existing code migrated gradually
    macroeconomics/                  new, independent first shared domain
  core/
    ingestion/
    quality/
    provenance/
    observations/
apps/api/src/                        generic versioned public endpoints
apps/dashboard/                      Fin Engine-only business presentation
contracts/
  inbound/riil-market-snapshot.v1.json
  outbound/indicator-latest.v1.json
```

These paths are **proposed**, not claims about current files. No mass rename of `riil_analysis` until necessary. Shared ingestion primitives should define a stable interface; specific domains own the actual semantics. Vehicle tables are not a substitute for generic indicator observations. A third-party customer should be able to use Fin Engine without access to Riil.

## 7. Reconciled development phases and release gates

| Gate | Riil independently | Fin Engine independently | Exchange / release gate |
| --- | --- | --- | --- |
| **0. Baselines** | Preserve existing site, D1, calculator reference tests, scheduled rates, article builds | Finalize feature branch, test API/dashboard + Python, verify Neon data and migrations | Both can build/run/deploy with integration turned **off** |
| **1A. Riil → FE: published data** | No change required initially; maintain existing public market JSON, dates and caveats | Build Riil inbound provider adapter + staged validated ingest and provenance | Fin Engine can ingest a Riil-published dataset with no Riil deployment dependency |
| **1B. Riil → FE: aggregate usage (optional)** | Decide lawful basis, disclosures, aggregation/suppression, data export rules and ownership; implement scheduled exporter only if approved | Separate aggregate contract, access controls and limited analytical storage | Approved aggregate feed only; **no raw calculator records** |
| **2. FE independent domains** | Keep current rate and Dampak workflows; no dependence on FE | Build native BI-Rate/JISDOR/BPS indicators from original authoritative sources and generic API | FE works without any Riil feed and independently verifies its outputs |
| **3. FE → Riil: shadow mode** | Add read-only inbound adapter after owner approval; compare FE values against existing workflow without publishing | Expose versioned, source-backed read-only responses | Match semantics, publication dates and accuracy; rollback verified |
| **4. FE → Riil: optional cutover** | Activate selected adapter feed, retain editorial override and last-known-good snapshots | Provide monitored API and freshness status | Riil can disable adapter without calculator, article or deployment failure |
| **5. Expand services** | Optional automotive context panels and other source-backed consumer features | Automotive/macro modules, audited B2B APIs, independent commercial deployment | No conflation of NJKB, market asks, auction limits or transaction prices |

There is **no obligation** to enable Gate 1B or the reverse feed before Fin Engine can progress with its own roadmap.

### Prioritization rationale

The first technical data exchange should start with Riil's **already-public market snapshots**: their structure, provenance and known caveats can be checked without moving personal data or rebuilding the Riil site. After a successful ingest, consider a separately governed aggregate insight product. Only later should Fin Engine become Riil's chosen data provider for specific indicators. This respects the desired order of data flow while minimizing coupling.

## 8. Privacy, commercial and data-integrity gates

- Riil and Fin Engine are separate systems even if their teams cooperate. Only the minimal approved field set crosses the boundary. Data sharing is not automatically permitted just because the same people developed both systems.
- Riil's privacy and account policies apply at collection. Update disclosures and evaluate applicable consent/lawful bases **before** enabling any usage-derived export or commercial redistribution. Financial behavior may remain sensitive in small groups. Never rely on stripping email alone as proof of anonymity.
- Do not send or store identifiers, raw calculator input payloads, contact details, per-user histories, session timestamps, or salary/debt combinations by default.
- Aggregate-feed safeguards should include defined cohort and metric dictionaries, minimum reporting thresholds, suppression for small groups, retention limits, role-based access, export audits, and no ability to query individual records.
- Distinguish **original source observations**, **Riil-curated summaries**, **Fin Engine calculations**, **synthetic demonstrations**, and **aggregate usage statistics**. Preserve origin and limitations in APIs and dashboards.
- BI-Rate is not a retail loan offer; Riil's SBDK sample currently represents a thin set of published bank floors, not an offered-market average. NJKB is not a retail selling price; asking listings are not realized transactions; auction limits are not final auction prices.
- Review publication/source licensing independently of data sensitivity. An item being publicly visible in Riil does not grant automatic commercial redistribution rights.

## 9. Integration governance and next implementation tickets

1. **Contract-first:** define a `riil.market_snapshot.v1` JSON Schema, sample fixtures and import validation tests in Fin Engine. Riil's current public artifact is the fixture; do not change Riil yet.
2. **Read-only Phase 1 importer:** create a source adapter in Fin Engine to ingest approved published Riil market snapshots, preserve original source provenance, and upsert/deduplicate according to stable observation identity. Run a dry-run preview, then persist to a **separate** indicator schema rather than vehicle tables.
3. **Prove independence:** exercise both projects with the adapter disabled, malformed feed, stale feed, and duplicated feed; add CI checks and an explicit compatibility/error report.
4. **Privacy/product gate for Phase 1B:** separately document any proposal to aggregate Riil's tracker data, including user disclosures and controls; do not export real behavior data without approval.
5. **Native data domain, then return path:** add independently sourced BI-Rate and other macro observations to Fin Engine, publish generic versioned APIs, then seek Riil-owner approval for a shadow inbound adapter and optional cutover.

**Change policy:** This document lives only in Fin Engine. Riil (`abagusdp/riil`) remains read-only; any future Riil code change needs separate approval and pull request. This update does not implement or activate transfers and makes no production database changes.
