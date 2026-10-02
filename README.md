# Fin Engine

B2B financial data and analysis platform for Riil.

Fin Engine turns vehicle-market and official reference data into traceable analytical signals for future collateral intelligence, valuation and underwriting-support products.

For a non-technical explanation of the product, target customers, use cases, data signals, limitations, commercial options and roadmap, see the [Business Overview](./docs/BUSINESS.md).

## Current status

Implemented:

```text
✓ TypeScript / Fastify public API
✓ Python / FastAPI analysis service
✓ Next.js / Tailwind / D3 business dashboard POC
✓ database-backed comparable valuation path
✓ dashboard → analysis-engine server-side integration
✓ official NJKB ingestion
✓ official DJP auction-limit ingestion
✓ authorized OLX / Mobil123 / Carmudi crawl framework
✓ authorized marketplace CSV feed adapters
✓ normalization + quality/audit pipeline
✓ Neon/PostgreSQL persistence
✓ Alembic migrations
✓ append-only observation history
✓ Bruno public API collection
```

Next infrastructure target:

```text
Cloud Run Jobs
→ Secret Manager
→ manual cloud crawl validation
→ Cloud Scheduler
→ populate observed marketplace history in Neon
```

Cloud Run Job infrastructure is **not yet committed/deployed**; see [Deployment](./docs/DEPLOYMENT.md).

## Architecture

```text
external sources
      ↓
Python adapters / crawlers
      ↓
normalization + quality
      ↓
Neon PostgreSQL
      ↓
Python analysis / feature engine
      ↓
┌──────────────────────┬──────────────────────┐
│ TypeScript public API│ Next.js dashboard    │
└──────────────────────┴──────────────────────┘
      ↓                         ↓
B2B API clients           business users
```

Python owns data acquisition, normalization, persistence and analytical domain logic. TypeScript owns the public API/control plane. The dashboard consumes analytical outputs and does not duplicate valuation formulas.

See [Architecture](./docs/ARCHITECTURE.md).

## Valuation data source

The Python valuation service now prefers persisted marketplace observations when `DATABASE_URL` is configured.

```text
DATABASE_URL configured
        ↓
latest listing observation per stable vehicle_record
        ↓
comparable_market_db_v1
```

Without `DATABASE_URL`, local development continues to use the committed sample comparable CSV:

```text
VEHICLE_DATA_PATH
        ↓
comparable_market_v1
```

This keeps development easy while allowing the same analysis endpoint to become genuinely observation-backed as Neon fills with authorized marketplace data.

## Data semantics

Fin Engine does not treat every vehicle value as the same type of price.

| `price_kind` | Meaning |
| --- | --- |
| `listing` | marketplace asking price |
| `njkb` | official NJKB reference value |
| `auction_limit` | published government auction limit/reserve-style value |
| `transaction` | reserved for future confirmed transaction prices |
| `reference` | generic reference signal when a stronger type does not apply |

These signal types remain distinguishable throughout ingestion, persistence, analysis and presentation.

## Repository layout

```text
fin-engine/
├── apps/
│   ├── api/                         # TypeScript / Fastify public API
│   ├── analysis/                    # Python analysis + ingestion + DB
│   └── dashboard/                   # Next.js business dashboard POC
├── bruno/                            # Git-tracked public API requests
├── contracts/                        # language-neutral public contracts
├── data/
│   ├── sample/                       # committed development fixtures
│   └── generated/                    # local generated output, Git-ignored
├── docs/                             # business + developer documentation
├── CONTRIBUTING.md
└── docker-compose.yml
```

## Quick start

Install dependencies:

```bash
yarn

cd apps/analysis
uv sync --extra dev
cd ../..
```

Python 3.12 is recommended.

### Run Python analysis service

```bash
cd apps/analysis
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
uv run uvicorn riil_analysis.main:app --reload --host 0.0.0.0 --port 8001
```

To use observed marketplace data instead, export a Neon `DATABASE_URL` in the same shell before starting the service.

### Run the business dashboard

In another terminal:

```bash
cp apps/dashboard/.env.example apps/dashboard/.env.local
yarn dev:dashboard
```

Open:

```text
http://localhost:3000
```

The dashboard calls the Python analysis service server-side. It visibly distinguishes:

```text
Analysis engine · Neon observations
Analysis engine · development comparables
Fallback POC data
```

Regional market context uses official BPS vehicle-stock data. The auction/downside signal remains explicitly illustrative until persisted auction data is exposed through analysis.

See [Business Dashboard](./docs/DASHBOARD.md).

### Run TypeScript public API

```bash
yarn dev:api
```

Test:

```bash
curl "http://localhost:8000/v1/vehicles/valuation?make=Toyota&model=Avanza&year=2023&region=Jakarta"
```

## Database

Fin Engine uses PostgreSQL for durable ingestion history. Neon is the initial hosted provider.

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@...-pooler....neon.tech/neondb?sslmode=require'

cd apps/analysis
uv run alembic upgrade head
```

Persist an ingestion run:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --persist-db
```

See [Database and Persistence](./docs/DATABASE.md).

## Ingestion sources

Current source IDs:

```text
kemendagri_njkb_2025
djp_vehicle_auction_limits

olx_authorized_crawl
mobil123_authorized_crawl
carmudi_authorized_crawl

olx_authorized_feed
mobil123_authorized_feed
carmudi_authorized_feed
```

Authorized marketplace crawlers are sequential and rate-limited. They require an authorization reference and do not implement CAPTCHA bypass, proxy rotation or access-control evasion.

Example:

```bash
cd apps/analysis
uv run fin-engine-data ingest \
  --source mobil123_authorized_crawl \
  --authorization-ref "permission-reference" \
  --request-delay-seconds 2 \
  --limit 5 \
  --persist-db \
  --output ../../data/generated/mobil123-small.csv
```

See [Ingestion](./docs/INGESTION.md) and [Source Registry](./docs/SOURCES.md).

## Testing

Python:

```bash
cd apps/analysis
uv run pytest -v
```

TypeScript API:

```bash
yarn typecheck:api
yarn build:api
```

Dashboard:

```bash
yarn typecheck:dashboard
yarn build:dashboard
```

The Bruno collection under `bruno/` contains executable public API examples/assertions. Public API route or contract changes must update Bruno in the same development pass.

## Documentation

- [Business Overview](./docs/BUSINESS.md)
- [Business Dashboard](./docs/DASHBOARD.md)
- [Documentation Index](./docs/README.md)
- [Local Development](./docs/DEVELOPMENT.md)
- [Architecture](./docs/ARCHITECTURE.md)
- [Ingestion](./docs/INGESTION.md)
- [Source Registry](./docs/SOURCES.md)
- [Database](./docs/DATABASE.md)
- [Testing](./docs/TESTING.md)
- [Deployment](./docs/DEPLOYMENT.md)
- [Contributing](./CONTRIBUTING.md)

## Core engineering rules

1. Keep public API/product concerns in TypeScript and analytical/data-domain logic in Python.
2. Preserve source provenance and `price_kind` semantics.
3. Keep observations append-only when history is analytically useful.
4. Do not claim cross-source physical-vehicle identity before entity resolution exists.
5. Use Alembic for deployed schema changes.
6. Keep live external-site calls out of normal unit tests.
7. Keep dashboard pages behind a server-side data-access boundary; never put analytical formulas or database credentials in browser code.
