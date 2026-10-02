# Fin Engine

B2B financial data and analysis platform for Riil.

Fin Engine turns vehicle-market and official reference data into traceable analytical signals for future collateral intelligence, valuation and underwriting-support products.

For a non-technical explanation of the product, target customers, use cases, data signals, limitations, commercial options and roadmap, see the [Business Overview](./docs/BUSINESS.md).

## Current status

Implemented:

```text
✓ TypeScript / Fastify public API
✓ Python / FastAPI analysis service
✓ vehicle comparable valuation development slice
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
```

Cloud Run Job infrastructure is **not yet committed/deployed**; see [Deployment](./docs/DEPLOYMENT.md) for the target design and rollout checklist.

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
TypeScript public API
      ↓
B2B clients
```

TypeScript owns public API/product infrastructure. Python owns data acquisition, normalization, persistence and analytical domain logic.

See [Architecture](./docs/ARCHITECTURE.md).

## Data semantics

Fin Engine does not treat every vehicle value as the same type of price.

| `price_kind` | Meaning |
| --- | --- |
| `listing` | marketplace asking price |
| `njkb` | official NJKB reference value |
| `auction_limit` | published government auction limit/reserve-style value |
| `transaction` | reserved for future confirmed transaction prices |
| `reference` | generic reference signal when a stronger type does not apply |

These signal types must remain distinguishable throughout ingestion, persistence and analysis.

## Repository layout

```text
fin-engine/
├── apps/
│   ├── api/                         # TypeScript / Fastify public API
│   └── analysis/                    # Python analysis + ingestion + DB
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

### Install dependencies

```bash
yarn

cd apps/analysis
uv sync --extra dev
```

Python 3.12 is recommended to match the current production container base.

### Run Python analysis service

```bash
cd apps/analysis
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
uv run uvicorn riil_analysis.main:app --reload --host 0.0.0.0 --port 8001
```

### Run TypeScript API

In another terminal, from the repository root:

```bash
yarn dev:api
```

Test:

```bash
curl "http://localhost:8000/v1/vehicles/valuation?make=Toyota&model=Avanza&year=2023&region=Jakarta"
```

## Database

Fin Engine uses PostgreSQL for durable ingestion history. Neon is the initial hosted provider.

Set a pooled Neon connection string:

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@...-pooler....neon.tech/neondb?sslmode=require'
```

Apply migrations:

```bash
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

Current source IDs include:

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

Authorized marketplace crawlers are sequential and rate-limited. They require an authorization reference and deliberately do not implement CAPTCHA bypass, proxy rotation or access-control evasion.

Example small crawl:

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

See [Ingestion and Source Adapters](./docs/INGESTION.md) and [Source Registry](./docs/SOURCES.md).

## Testing

Python:

```bash
cd apps/analysis
uv run pytest -v
```

TypeScript:

```bash
yarn typecheck:api
yarn build:api
```

The Bruno collection under `bruno/` contains executable examples/assertions for the public API.

Rule: when a public API route or contract changes, update Bruno in the same development pass.

See [Testing](./docs/TESTING.md).

## Documentation

- [Business Overview](./docs/BUSINESS.md) — non-technical product, customer, use-case and commercial context
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
7. Keep the README concise; put detailed business and operational guidance in `docs/`.