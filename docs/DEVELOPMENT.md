# Local Development

This guide is the fastest path from a fresh clone to a working Fin Engine development environment.

## Prerequisites

- Git
- Node.js 20+
- Yarn 1.22.x
- Python 3.12+
- `uv`
- Docker Desktop or another Docker Compose-compatible runtime, optional
- Neon/PostgreSQL only when testing persistence

The repository currently contains two runtime applications:

```text
apps/api       TypeScript / Fastify public API
apps/analysis  Python / FastAPI, ingestion, normalization, persistence
```

## Clone and bootstrap

```bash
git clone https://github.com/kevinkent1505/fin-engine.git
cd fin-engine
```

Install the TypeScript dependencies:

```bash
yarn
```

Install the Python dependencies:

```bash
cd apps/analysis
uv sync --extra dev
cd ../..
```

### Recommended Python version

Production containers currently use Python 3.12. Keep local development aligned with that version:

```bash
cd apps/analysis
uv python install 3.12
uv python pin 3.12
uv sync --extra dev
```

Verify:

```bash
uv run python --version
```

## Environment variables

Copy `.env.example` as a reference. Do not commit real credentials.

Current variables:

| Variable | Used by | Purpose |
| --- | --- | --- |
| `ANALYSIS_BASE_URL` | TypeScript API | Internal Python analysis-service URL |
| `VEHICLE_DATA_PATH` | Python analysis | Development comparable-data CSV |
| `DATABASE_URL` | Python ingestion/persistence | Neon/PostgreSQL connection string |

For local API development, a typical setup is:

```bash
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
```

For Neon persistence:

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@HOST-pooler.../neondb?sslmode=require'
```

Prefer Neon's pooled endpoint for short-lived/serverless clients.

## Run the services locally

### Terminal 1: Python analysis service

From `apps/analysis`:

```bash
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
uv run uvicorn riil_analysis.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8001
```

Check it:

```bash
curl http://localhost:8001/health
```

### Terminal 2: TypeScript public API

From the repository root:

```bash
yarn dev:api
```

Check it:

```bash
curl http://localhost:8000/health
```

Test the current public valuation endpoint:

```bash
curl "http://localhost:8000/v1/vehicles/valuation?make=Toyota&model=Avanza&year=2023&region=Jakarta"
```

## Bruno

The Git-tracked Bruno collection is under `bruno/`.

Open that directory in Bruno and select the `local` environment.

Development rule: **every public API route or contract change must update the corresponding Bruno request and assertions in the same development pass.**

Internal CLI ingestion commands do not need Bruno requests unless they become public HTTP endpoints.

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

This currently runs the public TypeScript API and Python FastAPI service. The ingestion CLI and future Cloud Run Jobs use the same Python package but are separate execution modes.

## Run tests

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

See [TESTING.md](./TESTING.md) for the testing strategy.

## Database setup

After setting `DATABASE_URL`:

```bash
cd apps/analysis
uv run alembic upgrade head
```

To inspect migration state:

```bash
uv run alembic current
uv run alembic history
```

See [DATABASE.md](./DATABASE.md) before changing tables.

## Run an ingestion source

NJKB with CSV output:

```bash
cd apps/analysis
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --output ../../data/generated/njkb-2025.csv
```

Persist directly to Neon:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --persist-db
```

Authorized marketplace crawl example:

```bash
uv run fin-engine-data ingest \
  --source mobil123_authorized_crawl \
  --authorization-ref "permission-reference" \
  --request-delay-seconds 2 \
  --limit 5 \
  --persist-db \
  --output ../../data/generated/mobil123-small.csv
```

See [INGESTION.md](./INGESTION.md) for source contracts and crawler rules.

## Generated data

`data/generated/` is intentionally ignored by Git. Use it for local inspection and debugging, not as the production source of truth.

Production-oriented ingestion should persist canonical observations to PostgreSQL.

## Common commands

```bash
# Python dependencies
cd apps/analysis && uv sync --extra dev

# Python tests
cd apps/analysis && uv run pytest -v

# API development
yarn dev:api

# API typecheck
yarn typecheck:api

# API build
yarn build:api

# Apply DB migrations
cd apps/analysis && uv run alembic upgrade head

# Show available ingestion sources
cd apps/analysis && uv run fin-engine-data ingest --help
```

## Troubleshooting

### Public API returns `502 analysis_unavailable`

The TypeScript API cannot reach the Python service. Confirm:

```bash
curl http://localhost:8001/health
```

When both services run locally, the TypeScript API expects `localhost:8001` unless `ANALYSIS_BASE_URL` overrides it.

### Database persistence says `DATABASE_URL is not set`

Set the variable in the same shell that runs the command:

```bash
export DATABASE_URL='...'
```

### Alembic cannot connect to Neon

Check that:

- the connection string is correct;
- `sslmode=require` is present when required;
- the password has not been accidentally shell-expanded;
- the Neon project/branch is active;
- you are using a compatible pooled endpoint.

### A marketplace crawl returns zero usable listings

Start with a narrow authorized URL and a small limit. A marketplace may change its HTML or JSON-LD structure. Do not work around access controls; update the source parser against the permitted page structure and add a regression test.
