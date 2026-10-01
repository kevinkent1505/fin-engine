# Fin Engine

B2B financial data and analysis platform for Riil.

## Architecture

Fin Engine now has durable PostgreSQL persistence:

```text
authorized crawler / official source
             ↓
      normalization + quality
             ↓
        Neon PostgreSQL
             ↓
      future feature engine
             ↓
      TypeScript public API
```

CSV remains available for local inspection, but PostgreSQL is the intended durable source of truth for scheduled cloud jobs.

## Data signals

Fin Engine keeps economic signals distinct:

```text
listing        marketplace asking price
njkb           official NJKB reference value
auction_limit  government auction limit
transaction    future confirmed transaction value
```

## Database model

The first migration creates:

```text
data_sources
    ↓
ingestion_runs

data_sources
    ↓
vehicle_records
    ↓
vehicle_observations
         ↑
    ingestion_runs
```

`vehicle_records` stores the stable identity of a record inside one source.

For marketplace sources, that normally means the marketplace listing ID. Fin Engine does **not** yet claim cross-source entity resolution.

`vehicle_observations` is append-only. If the same listing is crawled repeatedly:

```text
Oct 1   Rp218m
Oct 2   Rp214m
Oct 3   Rp214m
```

all observations are retained. This enables later features such as price reductions, days observed, price volatility and listing persistence.

## Neon setup

Create a Neon PostgreSQL project in a region close to the future Cloud Run deployment.

In Neon Connection Details, use the **pooled connection string** and expose it locally as:

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@...-pooler....neon.tech/neondb?sslmode=require'
```

Do not commit the real connection string.

Install/update dependencies:

```bash
cd apps/analysis
uv sync --extra dev
```

Create the schema:

```bash
uv run alembic upgrade head
```

## Persist an ingestion run

You can export CSV and persist to Neon in the same run:

```bash
uv run fin-engine-data ingest \
  --source olx_authorized_crawl \
  --authorization-ref "your-permission-reference" \
  --request-delay-seconds 2.0 \
  --limit 5 \
  --persist-db \
  --output ../../data/generated/olx-listings-small.csv
```

For Cloud Run Jobs, the CSV can be omitted:

```bash
uv run fin-engine-data ingest \
  --source olx_authorized_crawl \
  --authorization-ref "your-permission-reference" \
  --request-delay-seconds 2.0 \
  --limit 5 \
  --persist-db
```

The command reads `DATABASE_URL` from the environment.

The JSON result contains the database run ID and counts for:

```text
created_records
updated_records
inserted_observations
```

## Marketplace crawler controls

Authorized live crawlers:

```text
olx_authorized_crawl
mobil123_authorized_crawl
carmudi_authorized_crawl
```

Current self-imposed limits:

```text
concurrency             1
default delay           2.0 sec/request
minimum delay           1.0 sec/request
default detail limit    10/run
hard detail limit       50/run
max discovery pages     5/run
429 / 503 handling      Retry-After + backoff
proxy rotation          none
CAPTCHA bypass          none
fingerprint evasion     none
```

Every crawl requires an authorization reference.

## Other sources

NJKB:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --persist-db
```

DJP auction limits:

```bash
uv run fin-engine-data ingest \
  --source djp_vehicle_auction_limits \
  --limit 5 \
  --persist-db
```

## Testing

```bash
cd apps/analysis
uv sync --extra dev
uv run pytest -v
```

Database persistence tests run against a temporary SQLite database, so the test suite does not need Neon credentials.

## Bruno

This change affects internal ingestion/persistence only. No public HTTP contract changed, so Bruno remains unchanged.

## Next milestone

1. Create the Neon project and run the first migration.
2. Persist one five-record marketplace crawl.
3. Verify repeated crawls create one stable `vehicle_record` plus multiple `vehicle_observations`.
4. Containerize the ingestion command as a Cloud Run Job.
5. Store `DATABASE_URL` and marketplace authorization references in Google Secret Manager.
6. Add Cloud Scheduler after the job is verified manually.
