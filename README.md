# Fin Engine

B2B financial data and analysis platform for Riil.

## Milestone 0

The first version proves one cross-language path:

```text
B2B client
    ↓
TypeScript / Fastify public API
    ↓
Python / FastAPI analysis service
    ↓
sample vehicle observations
```

It intentionally does **not** include a scraper, database, queue, Redis, object storage, machine learning, or Kubernetes yet.

The first goal is to prove that a public API can ask the Python analysis engine for a traceable vehicle market valuation.

## Language boundary

**TypeScript owns API/product infrastructure:** public endpoints, validation, and later API keys, tenants, usage and billing.

**Python owns analytical domain logic:** future scraping, normalization, quality, features, valuation, statistics and ML.

Do not split analytical business logic across both languages.

## Structure

```text
fin-engine/
├── apps/
│   ├── api/                  # TypeScript / Fastify
│   └── analysis/             # Python / FastAPI + Polars
├── contracts/                # language-neutral public contracts
├── data/
│   └── sample/               # synthetic development data
├── docker-compose.yml
└── README.md
```

## Run

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

**Development rule:** when a public API route or contract is added or changed, update the corresponding
Bruno request and assertions in the same development pass. This keeps the executable API examples
versioned with the implementation.

## Python development

From `apps/analysis`:

```bash
uv sync --extra dev
uv run pytest
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
uv run uvicorn riil_analysis.main:app --reload --port 8001
```

## TypeScript development

Run the Python service on port 8001, then from the repository root:

```bash
yarn
yarn dev:api
```

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

After this path runs reliably, add **one permitted vehicle source**:

```text
one source
   ↓
scraper adapter
   ↓
raw observations
   ↓
normalization
   ↓
same Python valuation engine
   ↓
same TypeScript public API
```

Only after that should PostgreSQL replace the CSV.

Kubernetes is intentionally deferred. Container boundaries keep the services independently deployable later without making Kubernetes a prerequisite for the MVP.