# Architecture

Fin Engine is a B2B financial-data and analysis platform. The codebase deliberately separates product/API concerns, presentation concerns and data/analytics concerns.

## System boundary

```text
External data sources
        ↓
Python source adapters
        ↓
RawVehicleObservation
        ↓
Normalization + quality
        ↓
CanonicalVehicleObservation
        ↓
Neon PostgreSQL
        ↓
Python analysis / feature engine
        ↓
TypeScript API / dashboard data layer
        ↓
B2B API clients + Next.js business dashboard
```

The current public valuation path still uses a small development CSV. PostgreSQL-backed analytical queries are the next evolution, not something the current API already does.

The current business dashboard is also intentionally in POC mode: it combines official public-reference data with clearly labeled illustrative market fixtures until live persisted observations are connected.

## Application ownership

### TypeScript public API: control plane

`apps/api` owns customer-facing API infrastructure:

- public HTTP endpoints;
- request validation;
- public response contracts;
- error mapping;
- request IDs;
- later: tenants, API keys, authorization, quotas, usage, billing and webhooks.

The current implementation uses Fastify and Zod.

### Next.js dashboard: business presentation plane

`apps/dashboard` owns the business-facing POC experience:

- executive overview;
- vehicle-intelligence presentation;
- regional market-intelligence presentation;
- provenance / methodology presentation;
- business-friendly charts and summaries;
- server-side dashboard data-access boundary.

The dashboard currently uses Next.js, Tailwind CSS and D3.

It must not own crawler code, normalization rules, valuation formulas or underwriting decision logic.

### Python: intelligence plane

`apps/analysis` owns analytical and data-domain behavior:

- source acquisition;
- crawling and feed ingestion;
- parsing;
- normalization;
- deduplication;
- quality/audit reporting;
- persistence;
- valuation;
- later: feature engineering, statistics, ML and geospatial analysis.

The current service uses FastAPI, Pydantic and Polars. Persistence uses SQLAlchemy 2, psycopg 3 and Alembic.

### Rule

Do not duplicate analytical formulas or normalization rules in TypeScript/Next.js.

Do not put tenant, billing or public API-product logic inside Python analytical modules.

Keep the dashboard behind a data-access boundary so UI routes do not depend directly on persistence implementation details.

## Repository layout

```text
fin-engine/
├── apps/
│   ├── api/                         # TypeScript / Fastify public API
│   ├── dashboard/                   # Next.js business dashboard POC
│   │   ├── app/                     # route/layout layer
│   │   ├── components/              # generic presentation primitives
│   │   ├── features/                # domain-specific dashboard features
│   │   └── lib/data/                # server-side data-access boundary
│   └── analysis/                    # Python intelligence/data service
│       ├── migrations/              # Alembic migrations
│       ├── riil_analysis/
│       │   ├── database/            # SQLAlchemy models + persistence
│       │   ├── ingestion/           # common ingestion contracts/pipeline
│       │   ├── normalization/       # canonicalization rules
│       │   ├── scrapers/            # source adapters + polite HTTP client
│       │   ├── cli.py               # fin-engine-data CLI
│       │   ├── main.py              # internal FastAPI service
│       │   └── valuation.py         # current comparable valuation
│       └── tests/
├── bruno/                            # executable public API examples
├── contracts/                        # language-neutral public contracts
├── data/
│   ├── sample/                       # committed synthetic/test data
│   └── generated/                    # local generated outputs, ignored
├── docs/
└── docker-compose.yml
```

See [DASHBOARD.md](./DASHBOARD.md) for the dashboard-specific structure.

## Public API flow

Current flow:

```text
GET /v1/vehicles/valuation
        ↓
Fastify query validation
        ↓
POST /internal/v1/vehicles/valuation
        ↓
Python FastAPI
        ↓
comparable_market_v1
        ↓
development CSV
```

This is intentionally simple and proves the cross-language contract.

The TypeScript API maps analytical outcomes into stable public errors:

```text
invalid query        → 400 invalid_request
no comparables       → 404 no_comparables
analysis unavailable → 502 analysis_unavailable
```

## Dashboard flow

Current POC flow:

```text
official public-reference fixtures
+ illustrative business fixtures
              ↓
apps/dashboard/lib/data/index.ts
              ↓
Next.js server pages
              ↓
React + D3 presentation components
```

Target flow:

```text
Neon / internal Fin Engine queries
              ↓
apps/dashboard/lib/data/index.ts
              ↓
Next.js server pages
              ↓
React + D3 presentation components
```

The route/page layer should not care which data source is behind `lib/data`.

## Ingestion flow

```text
source adapter
    ↓
RawVehicleObservation
    ↓
normalize_records()
    ↓
CanonicalVehicleObservation
    ↓
quality + audit
    ↓
optional CSV
    ↓
optional PostgreSQL persistence
```

A source adapter is responsible only for source-specific acquisition/parsing. It should not implement valuation logic.

Normalization is responsible for turning source-specific values into consistent types and labels while preserving provenance.

Persistence is responsible for recording source identity, run metadata, stable source records and append-only observations.

## Economic signal types

A core architecture rule is that not every numeric vehicle value means the same thing.

Current `price_kind` values:

| Value | Meaning |
| --- | --- |
| `listing` | marketplace asking price |
| `njkb` | official Indonesian NJKB reference value |
| `auction_limit` | published government auction limit/reserve-style value |
| `transaction` | reserved for future confirmed transaction values |
| `reference` | generic reference value when a source does not fit a stronger type |

Never silently merge these into one undifferentiated "market price" column in analytical logic or dashboard presentation.

A future feature engine may compare signals, for example:

```text
listing_to_njkb_ratio
auction_limit_to_njkb_ratio
auction_discount_to_listing_median
```

but provenance and signal type must remain available.

## Source identity versus real-world vehicle identity

`vehicle_records` currently identifies a record **inside a source**.

Example:

```text
source_key       = olx_authorized_crawl
source_record_id = 123456789
```

This is not yet a universal vehicle ID. Two listings for the same physical car on two marketplaces remain separate records.

Cross-source entity resolution is a future capability and should not be inferred from matching make/model/year alone.

## Observation history

Vehicle observations are append-only by ingestion run.

```text
vehicle_record
   ├── observation at T1
   ├── observation at T2
   └── observation at T3
```

This preserves price history and enables future features such as:

- days observed;
- price reductions;
- relisting patterns;
- listing persistence;
- price volatility;
- market liquidity proxies.

## Database boundary

PostgreSQL is the durable data store. CSV is a developer/export surface.

The database currently contains:

```text
data_sources
 ingestion_runs
 vehicle_records
 vehicle_observations
```

See [DATABASE.md](./DATABASE.md).

## Crawler execution model

Marketplace crawlers are designed to be polite and sequential:

```text
concurrency             1
default delay           2 seconds
minimum delay           1 second
default detail limit    10/run
hard detail limit       50/run
max discovery pages     5/run
429 / 503               Retry-After + backoff
```

No proxy rotation, CAPTCHA bypass or access-control evasion is implemented.

See [INGESTION.md](./INGESTION.md).

## Deployment direction

The intended batch architecture is:

```text
Cloud Scheduler
      ↓
Cloud Run Job
      ↓
source adapter
      ↓
normalization + persistence
      ↓
Neon PostgreSQL
```

Important: the repository currently has the persistence layer, but a dedicated Cloud Run Job image/configuration has not yet been committed. Treat Cloud Run as the deployment target, not as an already-live component.

The dashboard deployment target can remain independent from batch ingestion. It can later be hosted on a Next.js-capable platform or Google Cloud once the product/deployment constraints are clearer.

See [DEPLOYMENT.md](./DEPLOYMENT.md).

## Design principles

1. **Provenance first.** Keep source ID, source record ID, source URL, observation time and parser metadata.
2. **Append observations.** Do not overwrite useful history.
3. **Separate signal semantics.** `listing`, `njkb`, `auction_limit` and `transaction` are not interchangeable.
4. **Keep source parsing isolated.** A marketplace layout change should not force changes throughout the analytical stack.
5. **Keep analytical logic in Python.** Public API and presentation concerns remain in TypeScript/Next.js.
6. **Keep presentation behind a data layer.** Dashboard routes should not know persistence implementation details.
7. **Prefer simple infrastructure until scale requires more.** PostgreSQL before ClickHouse; sequential jobs before Kafka/Kubernetes.
8. **Version interfaces, not implementation details.** Public API and source contracts should be explicit and testable.

## Planned evolution

Near-term:

```text
Cloud Run Jobs
→ scheduled multi-source collection
→ PostgreSQL-backed feature queries
→ replace dashboard POC fixtures with observed data
→ market-comparable valuation
→ API authentication and tenant layer
```

Later, only when justified by workload:

```text
object storage for raw payloads
Redis for caching/job state
PostGIS for geographic analysis
ClickHouse for high-volume analytical workloads
message queue/event streaming
Kubernetes
```
