# External data source registry

Fin Engine keeps source-specific acquisition separate from normalization and analytics.

## Source policy

Before a source is used in a commercial B2B product, review:

- access terms and Terms of Service;
- robots policy where applicable;
- licensing and reuse rights;
- rate limits;
- whether the source permits automated access;
- whether personal data is present;
- retention and attribution requirements.

Do not bypass CAPTCHA, authentication, paywalls, or technical access controls.

## Marketplace source review

### OLX Indonesia

Current published OLX terms prohibit use of robots, spiders and other automated mechanisms to access the service or monitor/copy its material, and prohibit automated scraping/data-mining except stated exceptions.

**Fin Engine decision:** no live crawler is implemented.

Supported integration path:

- approved API/feed;
- partnership export;
- written permission;
- other documented authorized data delivery.

Use source ID: `olx_authorized_feed`.

### Mobil123

Current published Mobil123 terms prohibit spiders, robots, crawlers and automated data retrieval, and exclude commercial aggregation of displayed listings and prices without company permission.

**Fin Engine decision:** no live crawler is implemented.

Supported integration path uses source ID: `mobil123_authorized_feed`.

### Carmudi Indonesia

Current published Carmudi terms prohibit automated retrieval/crawling and exclude commercial aggregation of displayed listings and prices without permission.

**Fin Engine decision:** no live crawler is implemented.

Supported integration path uses source ID: `carmudi_authorized_feed`.

## Authorized marketplace feed contract

All three authorized marketplace adapters accept the same CSV contract:

```text
listing_id
listing_url
make
model
variant
year
price
region
mileage_km
transmission
fuel
seller_type
observed_at
currency
```

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

The import deliberately excludes seller names, phone numbers and other personal contact fields from the canonical feed contract.

Each run must provide an authorization reference, such as a contract ID, partnership ticket, written permission reference or approved feed/API agreement. That reference is stored in each observation's provenance metadata.

## kemendagri_njkb_2025

**Source ID:** `kemendagri_njkb_2025`

**Publisher:** Kementerian Dalam Negeri Republik Indonesia

**Classification:** `price_kind = "njkb"`

NJKB is an official tax/reference value, not a marketplace listing or transaction price.

## djp_vehicle_auction_limits

**Source ID:** `djp_vehicle_auction_limits`

**Publisher:** Direktorat Jenderal Pajak, Kementerian Keuangan Republik Indonesia

**Classification:** `price_kind = "auction_limit"`

Auction limit is a reserve/floor-style signal, not a retail asking price or final transaction price.
