# Architecture

Fin Engine is a B2B financial-data and analysis platform. The codebase deliberately separates public-product concerns, business presentation, and analytical/data-domain logic.

## System boundary

```text
External data sources
        ↓
Python source adapters / crawlers
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
┌─────────────────────┬─────────────────────────┐
│ TypeScript public API│ Next.js dashboard server│
└─────────────────────┴─────────────────────────┘
        ↓                         ↓
 B2B API clients            business users
```

## Application ownership

### `apps/api`: TypeScript control plane

Owns customer-facing API behavior:

- public HTTP endpoints;
- request validation;
- public response contracts;
- stable error mapping;
- request IDs;
- later: tenants, API keys, authorization, quotas, usage, billing and webhooks.

Fastify and Zod are used here.

### `apps/dashboard`: business presentation plane

Owns:

- executive overview;
- vehicle-intelligence presentation;
- regional public-data context;
- provenance/methodology presentation;
- responsive, accessible D3 visualizations;
- server-side analytical data adapter.

The dashboard uses Next.js, React, Tailwind CSS and D3.

For the POC it calls the internal Python analysis endpoint server-side. Browser code does not receive Neon credentials or the internal analysis URL.

The dashboard must not own crawler logic, SQL persistence logic, normalization rules, valuation formulas or underwriting rules.

### `apps/analysis`: Python intelligence plane

Owns:

- source acquisition;
- crawling and feed ingestion;
- parsing and normalization;
- data-quality/audit logic;
- PostgreSQL persistence;
- comparable valuation;
- later: features, statistics, ML and geospatial analysis.

FastAPI, Pydantic and Polars are used for analysis/data work. Persistence uses SQLAlchemy 2, psycopg 3 and Alembic.

## Repository layout

```text
fin-engine/
├── apps/
│   ├── api/                         # Fastify public API
│   ├── dashboard/                   # Next.js business dashboard
│   │   ├── app/                     # routes/layout
│   │   ├── components/              # shell + generic UI
│   │   ├── features/                # domain-specific visualizations
│   │   └── lib/data/                # server-side analysis/data boundary
│   └── analysis/                    # Python intelligence plane
│       ├── migrations/
│       ├── riil_analysis/
│       │   ├── database/
│       │   ├── ingestion/
│       │   ├── normalization/
│       │   ├── scrapers/
│       │   ├── cli.py
│       │   ├── main.py
│       │   └── valuation.py
│       └── tests/
├── bruno/
├── contracts/
├── data/
│   ├── sample/
│   └── generated/
├── docs/
└── docker-compose.yml
```

## Public API valuation flow

```text
GET /v1/vehicles/valuation
        ↓
Fastify query validation
        ↓
POST /internal/v1/vehicles/valuation
        ↓
Python FastAPI
        ↓
valuation source selection
```

When the Python process has `DATABASE_URL` configured:

```text
Neon/PostgreSQL
      ↓
latest `listing` observation per vehicle_record
      ↓
comparable_market_db_v1
```

Without `DATABASE_URL`:

```text
data/sample/vehicles.csv
      ↓
comparable_market_v1
```

The public TypeScript API contract remains stable regardless of which internal source path is used.

Public error mapping remains:

```text
invalid query        → 400 invalid_request
no comparables       → 404 no_comparables
analysis unavailable → 502 analysis_unavailable
```

## Why valuation selects the latest listing observation

Ingestion history is append-only. The same marketplace listing may therefore have many observations over time.

A current valuation snapshot should not count that same listing repeatedly merely because it was crawled on multiple days. Database-backed comparable valuation therefore selects the latest `listing` observation per stable `vehicle_record` before calculating median / range statistics.

This preserves history in storage while avoiding crawl-frequency bias in a current snapshot.

## Dashboard flow

Current POC path:

```text
Next.js server page
      ↓
apps/dashboard/lib/data/index.ts
      ↓
apps/dashboard/lib/data/analysis.ts
      ↓
POST Python /internal/v1/vehicles/valuation
      ↓
DB-backed or development comparable valuation
```

The dashboard composes that analytical result with official public-reference context such as BPS vehicle counts and Kemendagri NJKB.

If the analysis service is unreachable or has no comparables, the dashboard uses an explicit fallback fixture and visibly labels the state `Fallback POC data`.

The dashboard never silently represents fallback data as observed marketplace output.

See [DASHBOARD.md](./DASHBOARD.md).

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
optional CSV export
    ↓
optional PostgreSQL persistence
```

A source adapter owns source acquisition/parsing only. It does not implement valuation logic.

## Economic signal types

Numeric vehicle values are not interchangeable.

| `price_kind` | Meaning |
| --- | --- |
| `listing` | marketplace asking price |
| `njkb` | official Indonesian NJKB reference |
| `auction_limit` | published auction limit/reserve-style value |
| `transaction` | future confirmed sale value |
| `reference` | generic reference when no stronger type applies |

Do not collapse these into an undifferentiated `market_price` field.

Future features may compare signals while retaining their semantics, for example:

```text
listing_to_njkb_ratio
auction_limit_to_njkb_ratio
auction_discount_to_listing_median
```

## Source identity versus physical-vehicle identity

`vehicle_records` identifies one stable record inside one source:

```text
source_key       = olx_authorized_crawl
source_record_id = 123456789
```

It is not a universal physical-vehicle ID. Two marketplaces may contain the same real car as separate records until explicit entity-resolution logic exists.

## Observation history

```text
vehicle_record
   ├── observation at T1
   ├── observation at T2
   └── observation at T3
```

This history supports future features such as days observed, price reductions, relisting behavior, listing persistence, volatility and liquidity proxies.

## Database boundary

PostgreSQL is the durable data store. CSV is a development/export surface.

Current tables:

```text
data_sources
ingestion_runs
vehicle_records
vehicle_observations
```

See [DATABASE.md](./DATABASE.md).

## Crawler execution model

Authorized marketplace crawlers are deliberately conservative:

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

## Deployment direction

Batch ingestion target:

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

The dashboard can be deployed independently on a Next.js-capable runtime and call the private/internal analysis service from its server environment.

Cloud Run Job infrastructure remains a deployment target until committed and deployed.

## Core design principles

1. **Provenance first.** Retain source, source record, source URL, observation time and parser metadata.
2. **Append useful history.** Do not overwrite analytically useful observations.
3. **Keep signal semantics distinct.** Listing, NJKB, auction and transaction evidence mean different things.
4. **Keep analytical truth in Python.** Dashboard and public API consume domain outputs.
5. **Keep browser code away from database credentials/internal secrets.**
6. **Avoid crawl-frequency bias.** Current valuation uses latest observations per stable listing.
7. **Prefer simple infrastructure until scale justifies more.** PostgreSQL before specialized analytical stores; sequential jobs before queues/Kubernetes.
8. **Keep interfaces testable.** Public API changes require Bruno updates; internal source/parsing changes require deterministic fixtures/tests.

## Planned evolution

Near-term:

```text
scheduled Cloud Run ingestion
→ more observed marketplace records in Neon
→ persisted auction query layer
→ true time-series endpoint
→ regional marketplace aggregation
→ dashboard search/filtering
→ API authentication and tenant layer
```

Later, only when justified:

```text
object storage for raw payloads
Redis for caching/job state
PostGIS
ClickHouse
message queues/event streaming
Kubernetes
```
