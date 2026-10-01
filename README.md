# Fin Engine

B2B financial data and analysis platform for Riil.

## Current milestone

The repository currently proves two architectural slices:

```text
PUBLIC QUERY PATH

B2B client
    ↓
TypeScript / Fastify public API
    ↓
Python / FastAPI analysis service
    ↓
sample vehicle observations
```

and:

```text
DATA INGESTION PATH

external source
    ↓
source adapter
    ↓
RawVehicleObservation
    ↓
normalization
    ↓
semantic quality checks
    ↓
CanonicalVehicleObservation
    ↓
CSV + audit JSON
```

The ingestion path is intentionally CLI-only for now. PostgreSQL, queues, object storage and Kubernetes remain deferred.

## Language boundary

**TypeScript owns API/product infrastructure:** public endpoints, validation, and later API keys, tenants, usage and billing.

**Python owns analytical domain logic:** scraping, ingestion, normalization, quality, features, valuation, statistics and ML.

Do not split analytical business logic across both languages.

## Run the API path

```bash
docker compose up --build
```

Try the public valuation:

```bash
curl "http://localhost:8000/v1/vehicles/valuation?make=Toyota&model=Avanza&year=2023&region=Jakarta"
```

The current public valuation still uses synthetic development comparables. NJKB reference data is deliberately kept separate.

## Bruno

The Git-tracked Bruno collection lives under `bruno/`.

When a **public** API route or contract changes, update Bruno in the same development pass. Internal ingestion commands remain CLI-only and do not need Bruno requests.

## Python development

From `apps/analysis`:

```bash
uv sync --extra dev
uv run pytest -v
```

## Official NJKB ingestion

Run:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --output ../../data/generated/njkb-2025.csv
```

The command now produces both:

```text
data/generated/njkb-2025.csv
data/generated/njkb-2025.audit.json
```

The CSV contains typed semantic fields in addition to the source value:

```text
njkb
weight_factor
dp_pkb
dp_pkb_expected
dp_pkb_difference
dp_pkb_check
```

For example, where the official record says:

```text
NJKB          = 214,000,000
weight        = 1.050
DP PKB        = 224,700,000
```

Fin Engine checks:

```text
214,000,000 × 1.050 = 224,700,000
```

and records `dp_pkb_check = pass` when the extracted relationship is consistent.

Semantic mismatches are **retained but flagged**. Structural failures are rejected and written to the audit JSON.

The audit file records:

- duplicate source record IDs;
- rejected record IDs and reasons;
- semantic-failure record IDs;
- the aggregate quality report.

The quality report now includes:

- total / valid / invalid records;
- duplicate records;
- missing prices;
- invalid years;
- normalization failures;
- semantic checks passed / failed / skipped.

## Vehicle type parsing

NJKB exposes an official vehicle `TYPE` string rather than clean model and variant fields.

Fin Engine now performs a conservative first-pass split, for example:

```text
AVANZA 1.5 VELOZ M/T (F654RM-GMSFJ)
→ model = Avanza
→ variant = 1.5 VELOZ M/T
```

The result is explicitly tagged in metadata as a heuristic with a confidence value. It is **not** treated as authoritative entity resolution.

A future vehicle master/catalog will replace this heuristic.

## Important data interpretation rule

`price_kind = "njkb"` means an official tax/reference value.

It must not be silently treated as:

- a marketplace listing price;
- a transaction price;
- a repossession/recovery price.

Future listing adapters will use `price_kind = "listing"`.

## Next milestone

After rerunning the full NJKB ingestion and reviewing semantic failures, select the first permitted market-listing source.

Then:

```text
market source
   ↓
RawVehicleObservation
   ↓
normalization + semantic quality
   ↓
first real listing dataset
   ↓
PostgreSQL
   ↓
comparable-market valuation
   ↓
same TypeScript public API
```

Kubernetes remains intentionally deferred.
