# Ingestion and Source Adapters

Fin Engine isolates source-specific acquisition from normalization, quality and analytics.

## Pipeline

```text
source-specific fetch
       ↓
source-specific parse
       ↓
RawVehicleObservation
       ↓
normalize_records()
       ↓
CanonicalVehicleObservation
       ↓
quality + audit
       ↓
CSV and/or PostgreSQL
```

A source adapter should know how to acquire and interpret **its own source**. It should not implement valuation or customer-facing API logic.

## Common source interface

Source adapters inherit from `VehicleSourceAdapter`.

The base interface provides configuration for:

```text
fetch_limit
authorization_reference
input_path
start_url
request_delay_seconds
```

Each concrete adapter implements:

```python
fetch() -> bytes
parse(payload: bytes) -> list[RawVehicleObservation]
```

`run()` simply calls `parse(fetch())`.

## Raw contract

All source adapters must emit `RawVehicleObservation`.

Core fields:

```text
source
source_record_id
source_url
observed_at

make_raw
model_raw
variant_raw
type_raw
year_raw
region_raw
price_raw

price_kind
currency
category_raw
metadata
```

### Preserve raw meaning

Do not silently reinterpret source values inside the adapter.

Examples:

```text
NJKB source       → price_kind = njkb
marketplace       → price_kind = listing
gov auction limit → price_kind = auction_limit
```

## Canonical contract

Normalization produces `CanonicalVehicleObservation`.

Important canonical fields:

```text
make
model
variant
type_name
year
region
price
price_kind
currency
category
```

NJKB-specific canonical fields include:

```text
njkb
weight_factor
dp_pkb
dp_pkb_expected
dp_pkb_difference
dp_pkb_check
```

Source-specific metadata remains available in the `metadata` object.

## Provenance requirements

Every source observation should retain enough context to trace it back to the source.

At minimum:

```text
source
source_record_id
source_url
observed_at
```

Where applicable, also preserve:

```text
parser_version
authorization_reference
access_basis
crawl delay
source row/coding
original source values
```

Do not remove raw/source metadata merely because a canonical equivalent exists.

## Quality and audit

The ingestion pipeline reports:

```text
total_records
valid_records
invalid_records
duplicate_records
missing_price_records
invalid_year_records
normalization_failures
semantic_checks_total
semantic_checks_passed
semantic_checks_failed
semantic_checks_skipped
```

The audit structure records:

```text
duplicate_record_ids
rejected_records
semantic_failure_record_ids
```

Structural failures are rejected. Semantic inconsistencies may be retained but explicitly flagged when preserving the source observation is useful.

### Example: NJKB semantic validation

For records where all fields are available:

```text
expected DP PKB = NJKB × weight factor
```

The normalizer compares extracted versus expected values and records the result.

## Registered sources

### Official/reference sources

```text
kemendagri_njkb_2025
djp_vehicle_auction_limits
```

### Authorized live marketplace crawlers

```text
olx_authorized_crawl
mobil123_authorized_crawl
carmudi_authorized_crawl
```

### Authorized marketplace feeds

```text
olx_authorized_feed
mobil123_authorized_feed
carmudi_authorized_feed
```

See [SOURCES.md](./SOURCES.md) for source governance and interpretation.

## Marketplace crawler policy

Authorized crawlers are intentionally conservative.

Current controls:

```text
concurrency             1
default request delay   2.0 seconds
minimum request delay   1.0 second
default detail limit    10/run
hard detail limit       50/run
max discovery pages     5/run
429 / 503               Retry-After + backoff
```

Not implemented:

```text
proxy rotation
CAPTCHA bypass
browser fingerprint evasion
access-control bypass
```

If the source-specific permission requires a slower rate or smaller scope, the stricter permission controls win.

Every authorized marketplace crawl requires `--authorization-ref`.

## Polite HTTP client

`PoliteHttpClient` provides:

- sequential requests;
- minimum delay enforcement;
- `Retry-After` handling;
- exponential-style backoff for 429/503;
- finite retries;
- a clear User-Agent.

Do not create a source adapter that silently bypasses this policy for the same marketplace crawl use case.

## Parsing strategy for marketplace pages

The generic authorized marketplace crawler prefers structured data when available:

1. JSON-LD vehicle/product fields;
2. visible page headings/title;
3. visible price/year/region text as fallback.

Useful fields include:

```text
make
model/descriptor
year
asking price
region
mileage
transmission
fuel type
```

Seller names, phone numbers, WhatsApp numbers and other seller contact details are intentionally excluded from the ingestion contract.

## Adding a new source

### 1. Define source semantics

Before coding, answer:

```text
What does the source value mean?
What should price_kind be?
What is the stable source_record_id?
What provenance must be retained?
What acquisition/access rules apply?
```

If none of the existing `PriceKind` values correctly represent the source, add a new explicit type rather than overloading an existing one.

### 2. Implement an adapter

Add a module under:

```text
apps/analysis/riil_analysis/scrapers/sources/
```

Subclass `VehicleSourceAdapter` and implement `fetch()` and `parse()`.

### 3. Register it

Add the adapter factory to:

```text
riil_analysis/scrapers/registry.py
```

This makes it available to:

```bash
uv run fin-engine-data ingest --source ...
```

### 4. Add normalization only when shared/canonical

Source-specific parsing belongs in the adapter.

Reusable canonicalization belongs in:

```text
riil_analysis/normalization/
```

Do not put site-specific CSS selectors or scraping rules in the normalizer.

### 5. Add tests

At minimum, test:

- a representative valid row/detail page;
- malformed or irrelevant source content;
- source-specific URL discovery if applicable;
- stable source ID behavior;
- correct `price_kind`;
- canonical normalization result;
- any source-specific semantic quality rule.

Prefer HTML/JSON fixtures embedded in tests rather than live network calls.

### 6. Update docs

Update:

```text
docs/SOURCES.md
docs/INGESTION.md when the common contract changes
README.md only if the source is important to first-time users
```

## Feed adapter contract

Authorized marketplace CSV feeds share a common schema.

Required:

```text
listing_id
listing_url
make
model
year
price
region
```

Optional:

```text
variant
mileage_km
transmission
fuel
seller_type
observed_at
currency
```

A template exists at:

```text
data/sample/authorized-marketplace-feed-template.csv
```

## CLI examples

### NJKB

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --persist-db
```

### Authorized marketplace crawl

```bash
uv run fin-engine-data ingest \
  --source olx_authorized_crawl \
  --authorization-ref "permission-reference" \
  --request-delay-seconds 2 \
  --limit 5 \
  --persist-db
```

### CSV plus DB

```bash
uv run fin-engine-data ingest \
  --source mobil123_authorized_crawl \
  --authorization-ref "permission-reference" \
  --limit 5 \
  --persist-db \
  --output ../../data/generated/mobil123-small.csv
```

## Failure behavior

A source adapter should fail clearly when:

- it cannot obtain a payload;
- the source layout no longer produces supported records;
- a required authorization reference is missing;
- a start URL points outside the adapter's permitted host;
- an input feed is malformed.

Do not silently return fabricated/default records.

One bad marketplace detail page may be skipped so that an otherwise healthy run can continue, but parser degradation should be visible through low valid counts and tests.

## Future improvements

Likely additions:

```text
raw payload/object-storage snapshots
parser version registry
source health metrics
per-source crawl checkpoints
listing disappearance tracking
cross-source vehicle entity resolution
```

These should build on the same provenance and canonical contracts rather than bypass them.
