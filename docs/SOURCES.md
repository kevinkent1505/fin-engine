# External Data Source Registry

Fin Engine keeps source-specific acquisition separate from normalization and analytics.

See [INGESTION.md](./INGESTION.md) for adapter contracts and [ARCHITECTURE.md](./ARCHITECTURE.md) for system-level data semantics.

## Registry

| Source ID | Provider/source | Signal | Acquisition | Status |
| --- | --- | --- | --- | --- |
| `bps_vehicle_stock_2025` | Badan Pusat Statistik | regional vehicle stock | official public statistics table | implemented |
| `kemendagri_njkb_2025` | Kemendagri / JDIH BPK | `njkb` | official PDF | implemented |
| `djp_vehicle_auction_limits` | Direktorat Jenderal Pajak | `auction_limit` | official public auction announcements | implemented |
| `marketplace_demo_seed` | Riil POC synthetic generator | `listing` | deterministic synthetic seed | implemented |
| `olx_authorized_crawl` | OLX Indonesia | `listing` | permission-gated live crawl | implemented |
| `mobil123_authorized_crawl` | Mobil123 | `listing` | permission-gated live crawl | implemented |
| `carmudi_authorized_crawl` | Carmudi Indonesia | `listing` | permission-gated live crawl | implemented |
| `olx_authorized_feed` | OLX Indonesia | `listing` | authorized CSV/feed | implemented |
| `mobil123_authorized_feed` | Mobil123 | `listing` | authorized CSV/feed | implemented |
| `carmudi_authorized_feed` | Carmudi Indonesia | `listing` | authorized CSV/feed | implemented |

`transaction` exists in the common price-kind contract but no confirmed transaction source is integrated yet.

## POC data policy

The public POC intentionally combines real official/open data with synthetic marketplace data:

```text
BPS regional vehicle stock     official / fetched from source
Kemendagri NJKB                official / fetched from source
DJP auction limits             official / fetched from source
Marketplace asking prices      synthetic POC seed
```

Synthetic marketplace rows must remain visibly labelled and must never be represented as scraped or observed marketplace evidence.

## `bps_vehicle_stock_2025`

Publisher/source:

```text
Badan Pusat Statistik (BPS - Statistics Indonesia)
Jumlah Kendaraan Bermotor Menurut Provinsi dan Jenis Kendaraan (unit), 2025
```

Acquisition:

```text
public BPS statistics table -> parser -> append-only Neon snapshot
```

Captured fields include:

```text
province
passenger cars
buses
trucks
motorcycles
total motor vehicles
```

This dataset is regional market context, not vehicle-level price evidence. It is persisted in `regional_vehicle_statistics`, separately from `vehicle_records` and `vehicle_observations`.

Run it with:

```bash
uv run fin-engine-data ingest \
  --source bps_vehicle_stock_2025 \
  --persist-db
```

The analysis service exposes the latest persisted snapshot at:

```text
GET /internal/v1/regional-market
```

The dashboard uses the persisted BPS snapshot when available and falls back to the committed static fixture only if the live-source snapshot is unavailable.

## Source policy

Before a source is used in a commercial B2B product, record:

- source owner/provider;
- access terms and permission basis;
- licensing/reuse rights;
- permitted request rate or crawl scope where specified;
- retention requirements;
- attribution requirements;
- whether personal data is present;
- stable source-record identifier strategy;
- economic meaning of the numeric value being collected.

Do not bypass CAPTCHA, authentication, paywalls or technical access controls.

If a source permission specifies stricter access limits than Fin Engine defaults, use the stricter source-specific limits.

## Economic interpretation

Do not treat these signals as interchangeable:

```text
listing
  asking price published by a marketplace seller/dealer, or a clearly-labelled
  synthetic asking-price observation when source = marketplace_demo_seed

njkb
  official Indonesian vehicle tax/reference value

auction_limit
  published auction limit/reserve-style value

transaction
  reserved for a future confirmed transaction/sale observation

reference
  generic reference value only when a stronger semantic type does not apply
```

Regional vehicle-stock statistics are contextual market-size indicators and do not use `price_kind`.

Analytical models may compare price signals, but must keep their origin and meaning available.

## `marketplace_demo_seed`

Purpose:

```text
POC demonstration only
```

This source generates deterministic synthetic marketplace-style asking-price observations for multiple makes, models and years. It exists so the business dashboard can demonstrate the complete ingestion → Neon → analysis → vehicle-selector flow before live marketplace collection is enabled.

It does **not** scrape OLX, Mobil123, Carmudi or any other marketplace, and its prices must not be represented as observed market evidence.

Canonical metadata includes:

```text
price_kind = listing
synthetic = true
access_basis = synthetic_demo
not_real_marketplace_observation = true
generator = marketplace_demo_v1
```

Run it with:

```bash
uv run fin-engine-data ingest \
  --source marketplace_demo_seed \
  --persist-db
```

The analysis service returns `comparable_market_demo_db_v1` when a selected vehicle is valued only from this source. If real persisted listing evidence exists for the same make/model/year/region, real listing sources take precedence and the synthetic rows are excluded from that valuation.

## Authorized live marketplace crawlers

Fin Engine supports live crawling of OLX Indonesia, Mobil123 and Carmudi only when the operator has explicit permission.

Source IDs:

```text
olx_authorized_crawl
mobil123_authorized_crawl
carmudi_authorized_crawl
```

Every run requires:

```text
--authorization-ref
```

The value is persisted as provenance. It should be a permission/contract/ticket reference, not credentials or the full permission document.

### Self-imposed crawler controls

```text
requests                sequential only
default delay           2.0 seconds
minimum delay           1.0 second
default detail limit    10/run
hard detail limit       50/run
max result pages        5/run
429 / 503               Retry-After + backoff
proxy rotation          none
CAPTCHA handling        none
access-control evasion  none
```

### OLX

Default start page:

```text
https://www.olx.co.id/mobil-bekas_c198
```

Canonical signal:

```text
price_kind = listing
```

Useful source fields may include make/model/year, asking price, location, mileage, transmission and fuel type when present in permitted page content.

### Mobil123

Default start page:

```text
https://www.mobil123.com/mobil-bekas-dijual
```

Canonical signal:

```text
price_kind = listing
```

### Carmudi

Default start page:

```text
https://www.carmudi.co.id/mobil-bekas-dijual/indonesia
```

Canonical signal:

```text
price_kind = listing
```

A narrower authorized search URL can be passed through `--start-url`.

## Authorized marketplace feed adapters

Source IDs:

```text
olx_authorized_feed
mobil123_authorized_feed
carmudi_authorized_feed
```

These are preferred when the marketplace provides an API, export or partner feed.

All three map to:

```text
price_kind = listing
access_basis = authorized_feed
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

Template:

```text
data/sample/authorized-marketplace-feed-template.csv
```

## `kemendagri_njkb_2025`

Publisher/source:

```text
Kementerian Dalam Negeri Republik Indonesia
Permendagri No. 7 Tahun 2025
JDIH BPK-hosted official document
```

Classification:

```text
price_kind = njkb
```

Captured data includes vehicle make/type, year, NJKB, weight factor and DP PKB where present.

Important limitation: NJKB is an official tax/reference value. It is not a marketplace asking price and is not a confirmed transaction price.

The ingestion pipeline performs source-specific semantic validation where enough fields exist:

```text
expected DP PKB ≈ NJKB × weight factor
```

The 2025 adapter remains available for reproducible historical/reference ingestion. A separate current-year adapter should be introduced rather than silently changing the semantics of this source ID.

## `djp_vehicle_auction_limits`

Publisher/source:

```text
Direktorat Jenderal Pajak
official auction announcements
```

Classification:

```text
price_kind = auction_limit
```

Captured data may include:

- make/type descriptor;
- production year;
- auction limit;
- deposit;
- mileage;
- auction date text;
- auction location text;
- announcement URL/title.

Important limitation: an auction limit is a reserve/floor-style signal. It is neither a retail asking price nor necessarily the final auction transaction price.

## Data minimization

The marketplace ingestion contract intentionally does not collect:

- seller names;
- phone numbers;
- WhatsApp numbers;
- other seller contact details.

Useful non-contact vehicle attributes may be retained when relevant:

```text
make
model
variant
year
price
region
mileage
transmission
fuel
seller_type
```

## Provenance expectations

Every persisted source observation should be traceable through source identity, source URL, observation time and ingestion run. Where applicable, provenance metadata should also preserve authorization basis, parser version and the raw source values used for canonicalization.

## Adding another source

Before implementing a new source, document it here with:

1. source ID;
2. source owner;
3. acquisition method;
4. permission/access basis;
5. stable record-ID strategy;
6. signal semantics;
7. important source-specific fields;
8. semantic limitations;
9. expected refresh frequency;
10. any stricter rate/retention rules.

Then follow the adapter workflow in [INGESTION.md](./INGESTION.md).


## Central source configuration

Official-source constants are managed in one place:

```text
apps/analysis/riil_analysis/config/sources.py
```

This registry owns:

- source IDs and stable semantic aliases;
- publisher names;
- canonical source and download URLs;
- release years and publication labels;
- HTTP timeouts and accepted content types;
- the shared Fin Engine user agent;
- default region values;
- marketplace request-delay defaults.

Application code should not hard-code annual source IDs such as
`kemendagri_njkb_2025` or `bps_vehicle_stock_2025`. Use the semantic aliases
`njkb_latest` and `vehicle_stock_latest`, or call
`latest_official_source(...)` from Python.

The standard refresh command is:

```bash
yarn refresh:official
```

It resolves the latest configured release for every official-source family at
runtime. Adding a new annual release should require adding its metadata to
`OFFICIAL_SOURCES`; adapters, dashboard queries, and the refresh command then
follow the new latest release automatically.

Year-specific source IDs are intentionally retained in the registry and
database for provenance. "Latest" is a runtime selection rule, not a destructive
rename of historical data.
