# Fin Engine

B2B financial data and analysis platform for Riil.

## Current data signals

```text
NJKB official reference
price_kind = njkb

Government auction limit
price_kind = auction_limit

Authorized marketplace crawl/feed
price_kind = listing
```

## Authorized live marketplace crawling

Fin Engine now includes permission-gated live crawlers for:

```text
olx_authorized_crawl
mobil123_authorized_crawl
carmudi_authorized_crawl
```

They are deliberately conservative:

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

### OLX small crawl

```bash
uv run fin-engine-data ingest \
  --source olx_authorized_crawl \
  --authorization-ref "your-permission-reference" \
  --start-url "https://www.olx.co.id/mobil-bekas_c198/q-toyota-avanza" \
  --request-delay-seconds 2.0 \
  --limit 5 \
  --output ../../data/generated/olx-listings-small.csv
```

### Mobil123 small crawl

```bash
uv run fin-engine-data ingest \
  --source mobil123_authorized_crawl \
  --authorization-ref "your-permission-reference" \
  --start-url "https://www.mobil123.com/mobil-dijual/toyota/avanza/indonesia_dki-jakarta" \
  --request-delay-seconds 2.0 \
  --limit 5 \
  --output ../../data/generated/mobil123-listings-small.csv
```

### Carmudi small crawl

```bash
uv run fin-engine-data ingest \
  --source carmudi_authorized_crawl \
  --authorization-ref "your-permission-reference" \
  --start-url "https://www.carmudi.co.id/mobil-bekas-dijual/indonesia" \
  --request-delay-seconds 2.0 \
  --limit 5 \
  --output ../../data/generated/carmudi-listings-small.csv
```

Use a larger delay if the permission specifies a stricter rate.

## Parsing approach

The crawler first discovers listing detail URLs from an authorized search/result page, then fetches detail pages sequentially.

It prefers structured JSON-LD fields when the marketplace publishes them and falls back to visible HTML text for:

- make;
- model/type;
- production year;
- asking price;
- region;
- mileage;
- transmission;
- fuel type.

Seller contact details are intentionally not collected.

Each record stores:

```text
price_kind = listing
access_basis = authorized_crawl
authorization_reference = ...
request_delay_seconds = ...
source_url = ...
```

## Authorized feed adapters

Feed/API/export ingestion remains available:

```text
olx_authorized_feed
mobil123_authorized_feed
carmudi_authorized_feed
```

See `data/sample/authorized-marketplace-feed-template.csv`.

## Other sources

Official NJKB:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --output ../../data/generated/njkb-2025.csv
```

Official DJP auction limits:

```bash
uv run fin-engine-data ingest \
  --source djp_vehicle_auction_limits \
  --output ../../data/generated/djp-auction-limits-small.csv \
  --limit 5
```

## Test

From `apps/analysis`:

```bash
uv sync --extra dev
uv run pytest -v
```

## Bruno

Marketplace ingestion remains CLI-only. No public HTTP contract changed, so Bruno does not need a new request in this pass.

## Next milestone

Validate each marketplace crawler with a five-record live run. Once at least one real listing source is stable, introduce PostgreSQL for repeated observations, provenance, deduplication and price history.

Keep `listing`, `njkb`, `auction_limit`, and future `transaction` signals distinct.
