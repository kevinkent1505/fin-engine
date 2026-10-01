# Fin Engine

B2B financial data and analysis platform for Riil.

## Current data signals

Fin Engine keeps different economic signals distinct:

```text
NJKB official reference
price_kind = njkb

Government auction limit
price_kind = auction_limit

Authorized retail marketplace feed
price_kind = listing
```

## Marketplace integrations

OLX, Mobil123 and Carmudi are now represented by **authorized-feed adapters**, not website crawlers.

Their current published terms restrict automated crawling/scraping and/or commercial aggregation of listings and prices without permission. Fin Engine therefore only accepts their data when delivered under a documented authorized arrangement.

Supported source IDs:

```text
olx_authorized_feed
mobil123_authorized_feed
carmudi_authorized_feed
```

A CSV template is available at:

```text
data/sample/authorized-marketplace-feed-template.csv
```

Required feed columns:

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

Run an authorized OLX feed, for example:

```bash
uv run fin-engine-data ingest \
  --source olx_authorized_feed \
  --input-file /path/to/approved-olx-feed.csv \
  --authorization-ref "contract-or-ticket-id" \
  --output ../../data/generated/olx-listings.csv
```

Mobil123:

```bash
uv run fin-engine-data ingest \
  --source mobil123_authorized_feed \
  --input-file /path/to/approved-mobil123-feed.csv \
  --authorization-ref "contract-or-ticket-id" \
  --output ../../data/generated/mobil123-listings.csv
```

Carmudi:

```bash
uv run fin-engine-data ingest \
  --source carmudi_authorized_feed \
  --input-file /path/to/approved-carmudi-feed.csv \
  --authorization-ref "contract-or-ticket-id" \
  --output ../../data/generated/carmudi-listings.csv
```

Each imported record keeps:

```text
price_kind = listing
access_basis = authorized_feed
authorization_reference = ...
```

The ingestion contract deliberately excludes seller names and contact details.

## Other ingestion sources

Official NJKB:

```bash
uv run fin-engine-data ingest \
  --source kemendagri_njkb_2025 \
  --output ../../data/generated/njkb-2025.csv
```

Official DJP auction-limit source:

```bash
uv run fin-engine-data ingest \
  --source djp_vehicle_auction_limits \
  --output ../../data/generated/djp-auction-limits-small.csv \
  --limit 5
```

## Bruno

Bruno remains synchronized with public HTTP APIs. These marketplace integrations are CLI ingestion sources, so no Bruno requests were added.

## Python development

From `apps/analysis`:

```bash
uv sync --extra dev
uv run pytest -v
```

## Next milestone

Once an approved marketplace feed is available and ingested, introduce PostgreSQL so Fin Engine can persist:

- source provenance;
- repeated listing observations;
- price history;
- NJKB reference values;
- auction-limit observations;
- deduplication keys;
- feature-engine outputs.

Do not silently combine `njkb`, `auction_limit`, `listing`, and future `transaction` observations; they represent different economic signals.
