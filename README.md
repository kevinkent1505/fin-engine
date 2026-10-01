# Fin Engine

B2B financial data and analysis platform for Riil.

## Current data signals

Fin Engine now separates three concepts instead of treating every number as a generic "price":

```text
NJKB official reference
price_kind = njkb

Government auction limit
price_kind = auction_limit

Retail marketplace asking price
price_kind = listing       # not connected yet
```

This distinction is intentional. An auction limit, NJKB reference and retail asking price represent different economic signals.

## Architecture

```text
external source
    ↓
source adapter
    ↓
RawVehicleObservation
    ↓
normalization
    ↓
semantic quality
    ↓
CanonicalVehicleObservation
    ↓
CSV + audit JSON
```

The public query path remains:

```text
B2B client
    ↓
TypeScript / Fastify API
    ↓
Python / FastAPI analysis
```

PostgreSQL, queues, object storage and Kubernetes remain deferred.

## Bruno

The Git-tracked Bruno collection lives under `bruno/`.

When a **public** API route or contract changes, update Bruno in the same development pass. The new auction ingestion is CLI-only, so this milestone does not change Bruno.

## Python development

From `apps/analysis`:

```bash
uv sync --extra dev
uv run pytest -v
```

## Official NJKB ingestion

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --output ../../data/generated/njkb-2025.csv
```

NJKB is stored with `price_kind = "njkb"` and receives its source-specific NJKB × weight / DP PKB semantic validation.

## Official DJP vehicle-auction limits

For a small development run:

```bash
uv run fin-engine-data ingest \
  --source djp_vehicle_auction_limits \
  --output ../../data/generated/djp-auction-limits-small.csv \
  --limit 5
```

The limit is applied to the source adapter before detail-page retrieval, so a five-record development run does not crawl 25 detail pages and discard 20 afterwards.

A successful row is classified as:

```text
price_kind = auction_limit
```

and may include metadata such as:

```text
deposit
mileage_km
auction_date_raw
auction_location_raw
announcement_title
```

The adapter intentionally ignores announcements that cannot be mapped confidently to one vehicle with a numeric auction limit.

## Source-governance decision

Fin Engine does not currently automate OLX, Mobil123 or Carmudi. Their published terms restrict automated scraping/crawling and/or commercial aggregation without permission.

For retail asking-price data, use a licensed feed/API, partnership, written permission, or another source with compatible terms rather than bypassing those restrictions.

See `docs/SOURCES.md`.

## Important interpretation rule

Do not silently combine:

```text
njkb
auction_limit
listing
transaction
```

They are different signals.

The future feature engine may compare them, for example:

```text
market_listing_to_njkb_ratio
auction_limit_to_njkb_ratio
auction_discount_to_market
```

but should retain provenance and signal type.

## Next milestone

Validate the DJP auction source locally. If it produces stable data, then introduce the first persistence layer (PostgreSQL) because Fin Engine will have multiple real source types with different provenance and observation history.

A retail marketplace adapter should be added only when an approved source is available.
