# Fin Engine

Independent financial data and intelligence platform. Riil is an initial potential data partner and future optional consumer, not a runtime dependency.

Fin Engine turns vehicle-market and official reference data into traceable analytical signals for future collateral intelligence, valuation and underwriting-support products.

For a non-technical explanation of the product, target customers, use cases, data signals, limitations, commercial options and roadmap, see the [Business Overview](./docs/BUSINESS.md).

For the cross-repository plan with Riil, see [Riil + Fin Engine Integration Roadmap](./docs/RIIL_INTEGRATION_ROADMAP.md). **Both products remain independently operable, developable and deployable.** Fin Engine obtains publicly available financial data **directly from original authorized sources**. Riil may later export **approved first-party usage and scenario signals** through a dedicated purpose-limited adapter, never by mirroring its private D1 database. In later phases Fin Engine may provide source-backed intelligence back to Riil through a separate adapter.

**No first-party Riil export has been activated.** The previously proposed Riil-public-market importer was retired because it duplicated data available from original providers. The generic market indicator migration remains for independently sourced datasets.

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

Cloud Run Job infrastructure is partially committed but deployment is not verified; see [Deployment](./docs/DEPLOYMENT.md).

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

## Automatic public data refresh

With a configured Neon `DATABASE_URL`, starting the Python analysis API (including `yarn dev`) starts a non-blocking background check for stale public NJKB, BPS and DJP data. It rechecks every 12 hours while running, and the GitHub Actions workflow `Refresh official public data` can perform weekly checks independently after you configure repository secret `FIN_ENGINE_DATABASE_URL`.

```bash
yarn refresh:data           # update only stale government sources
yarn refresh:data --force   # re-fetch all public sources
```

The scheduler uses successful `ingestion_runs` in Neon as freshness evidence and uses a database advisory lock to avoid duplicate concurrent work. Marketplace crawling remains explicit and permission-gated. Review [Local Development](./docs/DEVELOPMENT.md) for configuration.

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

Run the commands below from the repository root. For platform-independent local development, use the Yarn wrapper; Docker continues to install Python with pip directly.

Install dependencies and configure your local connection:

```bash
yarn
yarn setup
cp .env.local.example .env.local
```

Edit the root `.env.local` file and set your real Neon `DATABASE_URL`.
Then verify the connection setting without revealing its value:

```bash
yarn env:check
yarn dev
```

The launcher automatically reads this Git-ignored file for all Python
ingestion, API, dashboard, and migration commands. Environment variables
already configured in the terminal take precedence over `.env.local`.
Python 3.12+, Node.js 20+, and Yarn 1 are required; no `uv` or Windows
`py` launcher is necessary.

### Run Python analysis service

```bash
yarn dev:analysis
```

For Neon-backed official datasets, set `DATABASE_URL` in the root `.env.local`. The launcher passes it to the service automatically.

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
# Configure DATABASE_URL in .env.local once, then:
yarn migrate upgrade head
```

Persist an ingestion run:

```bash
yarn ingest --source njkb_latest --persist-db
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
yarn ingest \
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
yarn test:analysis -v
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
