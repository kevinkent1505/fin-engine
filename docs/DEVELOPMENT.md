# Local Development

This guide is the fastest path from a fresh clone to a working Fin Engine development environment.

## Prerequisites

- Git
- Node.js 20+
- Yarn 1.22.x
- Python 3.12+
- `uv`
- Docker Desktop or another Docker Compose-compatible runtime, optional
- Neon/PostgreSQL when testing database-backed valuation/persistence

The repository currently contains three application surfaces:

```text
apps/api        TypeScript / Fastify public API
apps/analysis   Python / FastAPI, ingestion, normalization, persistence, valuation
apps/dashboard  Next.js / Tailwind / D3 business dashboard POC
```

## Clone and bootstrap

```bash
git clone https://github.com/kevinkent1505/fin-engine.git
cd fin-engine
yarn

cd apps/analysis
uv python install 3.12
uv python pin 3.12
uv sync --extra dev
cd ../..
```

## Environment variables

Do not commit real credentials.

| Variable | Used by | Purpose |
| --- | --- | --- |
| `ANALYSIS_BASE_URL` | TypeScript API + dashboard server | Python analysis-service URL |
| `VEHICLE_DATA_PATH` | Python analysis | Development comparable CSV when no DB is configured |
| `DATABASE_URL` | Python analysis + ingestion | Neon/PostgreSQL connection; also enables DB-backed valuation |
| `DASHBOARD_VEHICLE_MAKE` | dashboard server | POC selected make |
| `DASHBOARD_VEHICLE_MODEL` | dashboard server | POC selected model |
| `DASHBOARD_VEHICLE_YEAR` | dashboard server | POC selected year |
| `DASHBOARD_VEHICLE_REGION` | dashboard server | POC selected region |

For the dashboard, start from:

```bash
cp apps/dashboard/.env.example apps/dashboard/.env.local
```

The dashboard's `ANALYSIS_BASE_URL` is server-side. Do not expose it as a `NEXT_PUBLIC_*` variable.

## Valuation data-source behavior

The Python valuation endpoint now has two explicit data paths:

```text
DATABASE_URL configured
        ↓
latest listing observation per vehicle_record
        ↓
PostgreSQL / Neon
        ↓
comparable_market_db_v1
```

If `DATABASE_URL` is not configured:

```text
VEHICLE_DATA_PATH
        ↓
committed development CSV
        ↓
comparable_market_v1
```

There is no silent DB-to-CSV fallback when a database is configured but has no comparables. The API returns no-comparables instead, allowing the dashboard to label its POC fallback honestly.

## Run locally

### Terminal 1: Python analysis service

From `apps/analysis`:

```bash
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
uv run uvicorn riil_analysis.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8001
```

Check:

```bash
curl http://localhost:8001/health
```

For database-backed valuation, export Neon first:

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@HOST-pooler.../neondb?sslmode=require'
```

Then restart the analysis service in the same shell.

### Terminal 2: business dashboard

From repository root:

```bash
yarn dev:dashboard
```

Open:

```text
http://localhost:3000
```

The dashboard calls the Python analysis service server-side. Its visible data-status panel reports one of:

```text
Analysis engine · Neon observations
Analysis engine · development comparables
Fallback POC data
```

Routes:

```text
/              Executive Overview
/vehicle       Vehicle Intelligence
/market        Market Intelligence
/methodology   Data & Methodology
```

See [DASHBOARD.md](./DASHBOARD.md).

### Terminal 3: TypeScript public API, when needed

```bash
yarn dev:api
```

Check:

```bash
curl http://localhost:8000/health
```

The dashboard does not require the public API for the POC analytical path. External/customer API contracts still belong in `apps/api`.

## Database setup

After setting `DATABASE_URL`:

```bash
cd apps/analysis
uv run alembic upgrade head
```

Inspect migration state:

```bash
uv run alembic current
uv run alembic history
```

See [DATABASE.md](./DATABASE.md).

## Populate observed marketplace data

A DB-backed dashboard needs listing observations in Neon that match the selected make/model/year/region.

Example authorized crawl:

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

The analysis endpoint uses only the latest listing observation per stable source record for a current comparable snapshot, so repeated crawls do not overweight the same listing.

See [INGESTION.md](./INGESTION.md).

## Tests and builds

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

Public API behavior should also be exercised through the Git-tracked Bruno collection under `bruno/`. Dashboard-only internal data-adapter changes do not require Bruno unless a public API contract changes.

## Docker Compose

```bash
docker compose up --build
```

Compose currently runs the public TypeScript API and Python analysis service. The dashboard is run directly through Next.js for the POC and is not yet included in Compose.

## Generated data

`data/generated/` is ignored by Git and intended for local inspection/debugging. Production-oriented canonical observations should persist to PostgreSQL.

## Troubleshooting

### Dashboard shows `Fallback POC data`

Check the analysis service first:

```bash
curl http://localhost:8001/health
```

Then confirm the dashboard server uses:

```text
ANALYSIS_BASE_URL=http://localhost:8001
```

If the analysis service is reachable but reports no comparables, either populate matching marketplace rows in Neon or change the dashboard POC vehicle selection to a segment that exists in the configured analysis source.

### Dashboard shows development comparables

The dashboard is connected to the Python analysis service, but that service does not have `DATABASE_URL` configured. This is valid for local development but must not be described as observed marketplace data.

### Public API returns `502 analysis_unavailable`

Confirm the Python service is running and that the API's `ANALYSIS_BASE_URL` is correct.

### Database persistence says `DATABASE_URL is not set`

Set the variable in the same shell that runs the command.

### Alembic cannot connect to Neon

Check the connection string, `sslmode=require`, shell escaping, Neon project state, and pooled endpoint.

### Marketplace crawl returns zero usable listings

Start with a narrow authorized URL and small limit. If page structure changed, update the parser and add a regression fixture rather than bypassing access controls.
