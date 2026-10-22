# Riil + Fin Engine: reconciled development roadmap

**Status:** proposed integration plan, 22 October 2026. Not an implementation claim.
**Fin Engine reference:** `kevinkent1505/fin-engine`, branch `feature/marketplace-poc`.
**Riil reference:** `abagusdp/riil`, branch `main` (read-only review).
**Design decision:** two repositories, separate release cycles, independent data stores, and versioned integration contracts. Fin Engine is a modular service/product in its own right, not Riil's backend implementation.

## 1. Product boundaries

**Riil (`riil.id`):** consumer money decisions, browser-side financial calculations, content and bilingual editorial publishing, user-facing explanation, CMS, account/saved-plan features, analytics/consent, Cloudflare Pages/Functions/D1. Riil owns the consumer interpretation, wording, product policies and release of its pages.

**Fin Engine:** reusable source adapters, official/public-data retrieval, quality and provenance, historical observations, standardized indicators, analytics and B2B product endpoints, operational ingestion, Neon/PostgreSQL, Python analysis, Fastify API, and its independent business dashboard. Fin Engine owns source semantics, ingestion schedules and database schema.

**Do not transfer ownership of:** Riil's `assets/riil.js`, `assets/engines/dampak.js`, HTML routes, Git-backed articles, CMS, auth, or D1 into Fin Engine. Preserve Riil's current static, no-framework calculator design. No cross-repository source imports, shared database connection, submodule, or direct Fin Engine commits to Riil.

**Deployment:** Riil remains deployable if Fin Engine is down; Fin Engine remains deployable and independently marketable without Riil. No direct browser-to-Neon path.

## 2. What exists today (repo-verified)

| Area | Riil | Fin Engine | Implication |
| --- | --- | --- | --- |
| Consumer calculations | Browser engines (`assets/riil.js`, `assets/engines/dampak.js`); engine reference tests | Python vehicle valuation | Keep consumer math in Riil. Do not duplicate a formula without independent contract tests. |
| Rates | `fetch-rates.py` + `rates.yml` refresh `data/market-rates.json` and the inlined `MARKET` block | No BI-Rate/SBDK domain yet | Best first read-only integration; dual-run before cutover. |
| Other market signals | CMS-controlled `data/market-snapshot.json`, built into `assets/dampak.js` | No general indicator-series model yet | Phase 2: one automated, verifiable source at a time, with editorial override. |
| Automotive data | Vehicle-loan calculator, related articles, and consumer context | Official NJKB, BPS vehicle stock, DJP auction values, authorized marketplace adapters; Neon history | Fin Engine supplies context or market references **with clear meanings**; Riil remains responsible for credit cash-flow arithmetic. |
| Editorial | Markdown, article builder, CMS, GitHub workflows and editorial standards | No CMS | Do not centralize article publication. Optionally supply cited fact packs with human review. |
| Analytics and personal data | D1 website tracker records event counters and finished calculator inputs; separate account/saved-calculation tables | No Riil event or identity subsystem | No raw D1 replication into Neon. Privacy and disclosure review required for any future analytics product. |
| API | Cloudflare Functions endpoints for CMS, accounts, analytics | Fastify public API; Python internal API | Add consumer-independent public indicators to Fastify; Riil consumes versioned output, never internal Python API. |

Evidence: `abagusdp/riil/README.md`, `docs/ARTICLE-ARCHITECTURE.md`, `docs/PLAN-DAMPAK-DOMPET.md`, `data/market-rates.json`, `data/market-snapshot.json`, `fetch-rates.py`, `.github/workflows/rates.yml`, `build-dampak.py`, `functions/_lib/insights.js`; and Fin Engine `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `apps/api/src/index.ts`, `apps/analysis/riil_analysis/main.py`.

## 3. Target architecture

```text
Official/public sources (BI, BPS, OJK, published market data, authorized marketplaces)
    |
    v
Fin Engine: source adapters + provenance + validation + historical observations
    |                      separate repository / deployments / Neon
    v
Fin Engine domain modules (macroeconomics, automotive, later other modules)
    |
    v
Fastify public API: stable versioned indicator/reference contracts
    |                                     |
    | build-time read-only snapshot       | authenticated B2B API
    v                                     v
Riil GitHub Actions adapter         Fin Engine B2B clients/dashboard
    |
    v
Riil's existing validated JSON snapshot(s)
    |  last-known-good on source failures
    v
Riil build scripts -> assets/riil.js MARKET + assets/dampak.js SNAPSHOT
    |
    v
Cloudflare Pages / Functions / D1 (consumer product)
```

**Initial integration uses a scheduled, read-only, build-time snapshot.** Riil does not need a live API call for basic public rate displays. A later authenticated Cloudflare server-side proxy may serve time-sensitive information when latency, freshness and access controls justify it. Do not make Riil's core calculator inputs dependent on the network.

## 4. Domain design within Fin Engine

Keep the existing three app processes for now; modularize *inside* the Python analysis app before considering separate domain microservices:

```text
apps/analysis/
  fin_engine/                        # proposed incremental destination; not present yet
    core/
      sources.py                      # registry, licensing/access metadata
      observations.py                 # provenance / temporal and quality primitives
      quality.py
      ingestion.py
    domains/
      automotive/                    # NJKB, auction, regional vehicle stock, valuation
      macroeconomics/                # BI-Rate, JISDOR, inflation; later SBDK
    providers/
      bank_indonesia/
      bps/
      ...
    service/
      indicators.py
  riil_analysis/                      # existing module; migrate incrementally
apps/api/                              # versioned external contracts + auth
apps/dashboard/                        # B2B/internal presentation only
contracts/                             # language-neutral API examples/schemas
```

Do not rename all existing modules at once. Add shared abstractions when the second non-automotive ingestion proves they are needed. Use compatibility imports during transitions. Domains must own their own models and tests; `vehicle_records` must not be repurposed as a generic indicator table.

**Data model for market indicators:** indicators (stable code, unit, economic definition), sources (publisher/URL/license/access restrictions), observations (as-of/period, fetched-at, value, source, source-run ID, original payload hash, revision/version), and ingestion runs with quality status. Differentiate event date, reference period, collection time, and publication time. Store revisions append-only. Add migrations, indexes and freshness rules explicitly.

## 5. API integration contract (proposed, not implemented)

First public capability, exposed by Fin Engine **Fastify**, not the Python internal API:

```http
GET /v1/indicators/bi_rate/latest
Accept: application/json
```

```json
{
  "schema_version": "1.0",
  "indicator": "bi_rate",
  "value": 5.75,
  "unit": "percent_per_year",
  "as_of": "YYYY-MM-DD",
  "published_at": "YYYY-MM-DD",
  "fetched_at": "YYYY-MM-DDTHH:mm:ssZ",
  "source": {
    "publisher": "Bank Indonesia",
    "url": "https://www.bi.go.id/id/statistik/indikator/BI-Rate.aspx"
  },
  "status": "verified",
  "caveat": "Policy rate; not a retail loan offer"
}
```

**All values and dates in this example are illustrative of the schema, not a current API response.**

Compatibility rules: UTC timestamps; ISO dates for source as-of and publication; explicit unit and semantic definition; source URL; `verified/stale/unavailable` status; no silent substitutions; versioned breaking changes; JSON Schema/OpenAPI plus contract tests in both repositories; ETag/cache policy; bounded API response time; rate limits/auth where warranted. Failed ingestion must preserve the previous validated observation and report freshness separately.

Riil's consumer-specific adapter **maps** the generic response into its current `data/market-rates.json` and, later, `data/market-snapshot.json` shape. This adapter belongs to Riil. Fin Engine must never write directly to Riil's GitHub repository or import Riil's UI code.

## 6. Phased reconciled roadmap

### Gate 0 — Baseline and independent stability

**Fin Engine:** finalize existing feature branch, migrate no production data without migration approval, TypeScript API/dashboard build + Python/tooling tests in CI, document deployment status accurately, and back up/check Neon. Keep synthetic marketplace listings labeled. Verify the BPS production snapshot is complete, not only that 39 rows exist.

**Riil:** preserve `main` deployment and the calculator-engine golden tests; document current `fetch-rates.py` output and `MARKET`-block synchronization; document snapshot build, CMS edit path, editorial validation and read-only integration contract.

**Done when:** both repos build independently; existing Riil numeric reference cases pass; no other repo needed to start or deploy either system.

### Gate 1 — BI-Rate as first shared financial indicator

**Fin Engine:** add macroeconomics domain/source adapter for official BI-Rate, append-only indicator observations, quality checks (value, date, source, detection of revisions), one stable Fastify endpoint with explicit provenance and tests, and a scheduled refresh mechanism.

**Riil:** keep `fetch-rates.py` and weekly workflow as the active producer while shadow-reading Fin Engine into a separately named comparison artifact. Compare rate, date, source and freshness over at least two successful updates or relevant publication changes. Avoid replacing `MARKET` with an unverified snapshot.

**Done when:** verified values agree within 0.01 percentage point for the same official publication, stale/failure behavior is tested, and rollback to the original rates producer is one configuration change.

### Gate 2 — Controlled Riil rates handoff

**Fin Engine:** publish stable read-only versioned indicator responses with deployment monitoring and last-known-good semantics.

**Riil:** change only the rate-fetch adapter to consume Fin Engine for **BI-Rate**, while retaining present `assets/riil.js` MARKET generation and calculator behavior. Do not move SBDK yet: the current Riil sample is one verified bank and explicitly **not a market lending-rate average**. Preserve that coverage note and Bank-specific provenance.

**Done when:** Riil can deploy and display last validated values if Fin Engine is down, existing rate disclosure language stays accurate, and no new user data is transmitted.

### Gate 3 — Broaden macro / Dampak market context

Prioritize **JISDOR USD/IDR**, then **BPS inflation**, then carefully assessed **gold/commodity, fuel and IHSG** feeds depending on licensing, quality and publication cadence. Add each Fin Engine adapter separately with source-specific schema, time semantics, data provenance, revisions and freshness checks. No scraping around WAFs or access controls.

Riil keeps the CMS `data/market-snapshot.json` as an editorial gate. Introduce a reviewed import from Fin Engine rather than overwriting manually curated or disputed values. `build-dampak.py` stays the canonical static asset publisher and validates exactly as before.

**Done when:** at least two independently validated indicators work from Fin Engine through Riil's existing static build, with clear staleness and a manual override.

### Gate 4 — Automotive crossover, without calculator migration

Offer optional published **vehicle market context** from Fin Engine (official NJKB tax/reference, regional BPS vehicle stocks, carefully qualified asking prices and auction limits). Pilot one opt-in Riil vehicle-page contextual panel or corresponding article facts without touching loan repayment math.

Do not equate NJKB with market sale value, listing price with verified transaction value, or auction limit with realized auction price. Synthetic listing data must never be presented as observed market evidence. An independent, tested Fin Engine API should expose sources, count, observed dates, geographic coverage and limitations.

**Done when:** vehicle context is source-backed, has a clear separation from calculator results, fails safely, and can be removed without breaking Riil.

### Gate 5 — Fin Engine as an independent data product

Harden public API keys/auth, usage controls, audit logs, quotas, availability, observability, rate-limited ingestion, retries, source terms/licensing and customer contracts. Mature the B2B dashboard and domain analytics. Only then consider extracting high-load ingestion workers or other domains into separately deployed services.

**Done when:** a third-party consumer can use Fin Engine without knowing Riil exists, and Riil continues to release independently.

## 7. Analytics, privacy and commercial boundary

Riil presently collects event counts and some completed calculation values into Cloudflare D1 while consumer calculation logic runs in the browser. Although Riil's tracker aims to avoid direct identifiers, small or unusual combinations of financial figures may still be privacy-sensitive. The repo's privacy promises, user disclosure/consent and applicable obligations govern any future usage.

**Default:** keep all Riil event, account and saved-calculation records in Riil/D1. Do **not** mirror raw calculator inputs, salary/debt amounts, email/account IDs, tracker events or per-person histories into Fin Engine/Neon.

Any future Fin Engine product based on aggregates of Riil usage requires a separate explicit product decision, lawful basis and updated disclosures before transfer or commercialization; privacy/security review, thresholding and suppression for small cohorts, retention/access controls, and a documented opt-out/deletion strategy. Do not infer that "anonymous by design" means unconditional permission to sell or share.

## 8. Branches, integration and rollout discipline

- Riil remains read-only from this Fin Engine workstream. Any future Riil modification requires repo-owner approval and a separate Riil PR.
- Fin Engine changes stay in feature branches with CI; do not couple the release of the two repositories. For API changes: schema and examples first, then tests, then producer deployment, then shadow consumer, then cutover.
- Consumer snapshot failures must leave the last-good Riil data and its as-of date intact. No auto-commit directly from Fin Engine to Riil, and no secret tokens in static assets, build logs or URLs.
- No synchronous call to Fin Engine for private Riil user input in the first integration. Avoid direct browser CORS connections; if a dynamic product later requires calls, use a Cloudflare Function server-side proxy with explicit auth, quotas, caching, timeouts and data-minimization rules.
- API or data-model migrations must support existing consumers through a deprecation window; keep contract fixtures in both repositories.

## 9. The next four implementation tickets

1. **Fin Engine CI + baseline:** complete TypeScript build/typecheck checks; run and document existing Python/tooling jobs; close branch readiness issues.
2. **Fin Engine macro domain:** design an indicator schema, database migration, official BI-Rate adapter and a stable `/v1/indicators/bi_rate/latest` endpoint, with source/temporal contract tests.
3. **Non-mutating Riil compatibility fixture:** add a contract fixture in Fin Engine that reproduces the **public, non-sensitive** fields currently needed by Riil's MARKET block. Do not modify the Riil repository yet.
4. **Riil PR only after approval:** add a shadow-mode, read-only adapter in Riil's rate refresh workflow, compare with `fetch-rates.py`, and document rollback; keep both brands independently deployable.

## 10. Decisions and anti-goals

- **Decision:** API boundary, not a merged repo, shared database, cross-repo package import or microservice explosion.
- **Decision:** use Fin Engine's existing Fastify as the public contract and Python as the internal analytics engine.
- **Decision:** Riil's calculations remain transparent, client-side and user-controlled.
- **Decision:** market data sourced in Fin Engine may power Riil, but Riil always controls editorial framing and publication.
- **Do not prioritize:** migrating all Riil pages to Next.js; moving Riil accounts, CMS or D1 to Neon; rewriting all calculators in Python; replacing all source adapters simultaneously; implementing B2B behavioral monetization before a privacy/consent review.

This is a roadmap alignment document. No Riil files, deployment settings, credentials or databases have been changed by writing it.
