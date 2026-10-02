# Testing

Fin Engine tests should protect contracts and data semantics, not only code paths.

## Test commands

Python:

```bash
cd apps/analysis
uv sync --extra dev
uv run pytest -v
```

TypeScript API:

```bash
yarn typecheck:api
yarn build:api
```

Business dashboard:

```bash
yarn typecheck:dashboard
yarn build:dashboard
```

Public HTTP behavior should also be exercised through the Git-tracked Bruno collection under `bruno/`.

## Current Python test areas

The suite covers:

- comparable valuation baseline;
- case-insensitive comparable matching;
- Indonesian currency/price normalization;
- category cleanup;
- NJKB semantic validation;
- semantic mismatch handling;
- model/variant heuristic behavior;
- deduplication and ingestion audit behavior;
- official NJKB parser behavior;
- rejection of unrelated PDF table rows;
- authorized marketplace feed mapping;
- authorized marketplace crawl parsing;
- detail-link discovery;
- crawler authorization and host restrictions;
- rate-limit floor behavior;
- DJP auction-limit parsing;
- PostgreSQL URL normalization;
- database identity/history persistence behavior.

## Dashboard checks

The dashboard currently relies primarily on TypeScript typechecking and production builds rather than a dedicated component-test framework.

At minimum, dashboard changes should verify:

```text
✓ yarn typecheck:dashboard
✓ yarn build:dashboard
✓ / renders
✓ /vehicle renders
✓ /market renders
✓ /methodology renders
✓ official vs illustrative labels remain visible
✓ no browser-side database credentials are introduced
```

When interactive filtering/search is added, introduce component/integration tests at the same time rather than relying only on build success.

The dashboard data layer should remain testable independently from pages. Keep data retrieval behind `apps/dashboard/lib/data/index.ts`.

## Test layers

### 1. Pure/unit tests

Use for deterministic logic:

```text
normalization
price parsing
model/variant heuristics
semantic checks
URL filtering
structured-data extraction
quality counters
formatting / derived dashboard helpers when added
```

These should not require network access.

### 2. Adapter fixture tests

A source parser should have representative source fixtures embedded in tests.

Examples:

```text
HTML detail page
HTML search/result page
CSV feed
PDF table row
```

The goal is to detect parser regressions without hitting live services in CI.

### 3. Persistence tests

Database tests currently use a temporary SQLite database for speed and isolation.

They verify behavior such as:

```text
first crawl  → create one stable source record + observation
second crawl → update stable record + append another observation
```

These tests do not prove every PostgreSQL-specific feature. PostgreSQL/Neon integration should be validated separately before deployment.

### 4. Public API contract tests

The Bruno collection is the executable developer-facing API example.

When changing a public route:

1. update implementation;
2. update language-neutral contract if applicable;
3. update Bruno request;
4. update Bruno assertions;
5. run TypeScript typecheck/build;
6. manually exercise the request locally.

### 5. Dashboard presentation/data-contract checks

The dashboard must preserve source semantics in presentation.

Do not allow:

```text
illustrative → displayed as observed
official NJKB → labeled as market transaction
auction_limit → labeled as sale price
listing → labeled as confirmed market value
```

When the dashboard moves to live data, add fixtures or contract tests for the internal dashboard query responses before adding more presentation complexity.

## No live network in normal unit tests

Do not make routine test execution dependent on OLX, Mobil123, Carmudi, DJP, BPK, BPS or other live external websites.

Reasons:

- layouts change;
- external availability is outside our control;
- rate limits should not be consumed by test suites;
- reproducibility matters;
- tests should not become accidental crawlers.

Use saved/minimal fixtures that reproduce the relevant structure.

## Adding a new source adapter

Required tests should normally include:

```text
✓ one valid source fixture
✓ one invalid/irrelevant fixture
✓ correct source_record_id
✓ correct price_kind
✓ correct source URL/provenance
✓ normalized make/model/year/price
✓ source-specific fields where relevant
✓ authorization/rate-limit behavior for restricted crawlers
```

If a production bug is discovered from a real page, reduce it to the smallest safe fixture that reproduces the bug and add that fixture as a regression test.

## Database migration testing

For schema changes:

```bash
cd apps/analysis
uv run alembic upgrade head
```

Before merging a non-trivial migration, verify it against a disposable PostgreSQL/Neon branch where practical.

Check:

- upgrade succeeds;
- expected indexes/constraints exist;
- persistence still works;
- existing rows remain interpretable;
- downgrade is safe if one is provided and intended to be used.

## Quality assertions versus exact counts

Avoid brittle tests against live-source total counts.

For live smoke tests, assertions such as these are more useful:

```text
total_records > 0
valid_records > 0
normalization_failures == 0 or investigated
semantic failure rate within expected bounds
```

For fixed unit fixtures, exact counts are appropriate.

## Manual live smoke tests

Use small limits first.

Example:

```bash
uv run fin-engine-data ingest \
  --source mobil123_authorized_crawl \
  --authorization-ref "permission-reference" \
  --request-delay-seconds 2 \
  --limit 5 \
  --output ../../data/generated/mobil123-smoke.csv
```

Inspect both:

```text
mobil123-smoke.csv
mobil123-smoke.audit.json
```

Only after the five-record run looks semantically correct should a larger run be attempted.

## Regression checklist

Before merging changes to ingestion or persistence:

```text
[ ] uv run pytest -v
[ ] no unexpected normalization failures
[ ] source semantics / price_kind unchanged or intentionally migrated
[ ] provenance still retained
[ ] DB history remains append-only
[ ] migration added if schema changed
[ ] docs updated if behavior/contract changed
```

Before merging public API changes:

```text
[ ] yarn typecheck:api
[ ] yarn build:api
[ ] Bruno updated
[ ] local success path tested
[ ] local error paths tested
```

Before merging dashboard changes:

```text
[ ] yarn typecheck:dashboard
[ ] yarn build:dashboard
[ ] key routes manually checked
[ ] official / observed / illustrative labeling remains correct
[ ] dashboard logic stays presentation-focused
[ ] docs updated when data interpretation changes
```

## CI direction

A future CI workflow should run at minimum:

```text
Python dependency sync
Python pytest
TypeScript dependency install
API typecheck + build
Dashboard typecheck + build
Alembic migration consistency check
```

Live marketplace crawling should remain outside ordinary CI.
