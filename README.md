# Fin Engine

B2B financial data and analysis platform for Riil.

## Current milestone

The repository now has two working architectural slices:

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
normalization + quality checks
    ↓
CanonicalVehicleObservation
    ↓
CSV export for inspection
```

The ingestion path is intentionally CLI-only for now. PostgreSQL, queues, object storage and Kubernetes remain deferred.

## Language boundary

**TypeScript owns API/product infrastructure:** public endpoints, validation, and later API keys, tenants, usage and billing.

**Python owns analytical domain logic:** scraping, ingestion, normalization, quality, features, valuation, statistics and ML.

Do not split analytical business logic across both languages.

## Structure

```text
fin-engine/
├── apps/
│   ├── api/                  # TypeScript / Fastify
│   └── analysis/
│       └── riil_analysis/
│           ├── ingestion/
│           ├── normalization/
│           ├── scrapers/
│           └── valuation.py
├── bruno/                    # Git-tracked public API requests
├── contracts/                # language-neutral public contracts
├── data/
│   ├── sample/               # synthetic development data
│   └── generated/            # local generated ingestion outputs; ignored by Git
├── docs/
│   └── SOURCES.md
└── docker-compose.yml
```

## Run the API path

Requirement: Docker Desktop or another Docker Compose-compatible runtime.

```bash
docker compose up --build
```

Public API:

```text
http://localhost:8000
```

Try the first valuation:

```bash
curl "http://localhost:8000/v1/vehicles/valuation?make=Toyota&model=Avanza&year=2023&region=Jakarta"
```

Expected analytical result inside the public response:

```json
{
  "vehicle": {
    "make": "Toyota",
    "model": "Avanza",
    "year": 2023
  },
  "region": "Jakarta",
  "valuation": {
    "estimate": 218000000,
    "low": 202000000,
    "high": 236000000
  },
  "sample_size": 13,
  "method": "comparable_market_v1"
}
```

The TypeScript API adds a unique `request_id`.

## Bruno API collection

The repository includes a Git-tracked Bruno collection under `bruno/`.

Open that directory in Bruno and select the `local` environment.

Current requests:

- API health;
- successful vehicle valuation;
- no-comparables response;
- invalid-request response.

The local environment uses:

```text
apiBaseUrl = http://localhost:8000
```

**Development rule:** when a public API route or contract is added or changed, update the corresponding Bruno request and assertions in the same development pass.

Internal batch/ingestion commands do not get Bruno requests unless they become public HTTP APIs.

## Python development

From `apps/analysis`:

```bash
uv sync --extra dev
uv run pytest
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
uv run uvicorn riil_analysis.main:app --reload --port 8001
```

## First real source: official 2025 NJKB reference

The first external adapter reads the official vehicle-value appendix in Permendagri No. 7 Tahun 2025 through JDIH BPK.

Run it from `apps/analysis`:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --output ../../data/generated/njkb-2025.csv
```

For a small development output:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --output ../../data/generated/njkb-2025-small.csv \
  --limit 50
```

The command prints a quality report containing:

- total records;
- valid records;
- invalid records;
- duplicates;
- missing prices;
- invalid years;
- normalization failures.

The generated CSV is ignored by Git.

**Important:** NJKB is an official tax/reference value, not a live listing or confirmed transaction price. The ingestion contract records it as `price_kind = "njkb"`. It must not be silently mixed into `comparable_market_v1`, which currently uses synthetic listing-style development data.

See `docs/SOURCES.md` for provenance and source policy.

## Current valuation method

`comparable_market_v1` deliberately does only:

1. match make;
2. match model;
3. match model year;
4. match region;
5. calculate median;
6. calculate p10 / p90;
7. return sample size.

The sample CSV is **synthetic development data**, not observed market data and not suitable for underwriting.

## Next milestone

Run and inspect the official-source ingestion locally, then select the first market-listing source whose automated-access and commercial-reuse conditions are acceptable.

After one real listing adapter is reliable:

```text
market source
   ↓
RawVehicleObservation
   ↓
normalization + quality
   ↓
PostgreSQL
   ↓
comparable-market valuation
   ↓
same public TypeScript API
```

PostgreSQL should be introduced only after the first market source gives us real schema requirements.

Kubernetes remains intentionally deferred. Container boundaries keep services independently deployable later without making Kubernetes a prerequisite for the MVP.
