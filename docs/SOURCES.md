# External data source registry

Fin Engine keeps source-specific acquisition separate from normalization and analytics.

## Source policy

Before a source is used in a commercial B2B product, record:

- access terms and the permission basis;
- licensing/reuse rights;
- permitted request rate or crawl scope where specified;
- retention and attribution requirements;
- whether personal data is present.

Do not bypass CAPTCHA, authentication, paywalls, or technical access controls.

## Authorized live marketplace crawlers

Fin Engine supports live crawling of OLX Indonesia, Mobil123, and Carmudi **only when the operator has explicit permission**.

Source IDs:

```text
olx_authorized_crawl
mobil123_authorized_crawl
carmudi_authorized_crawl
```

Every run requires `--authorization-ref`. This is stored in record provenance.

The crawler deliberately applies these self-imposed controls:

- sequential requests only;
- default 2.0 seconds between requests;
- minimum configurable delay of 1.0 second;
- default 10 detail pages per run;
- hard cap of 50 detail pages per run;
- maximum five result/index pages per run;
- retry/backoff for HTTP 429 and 503;
- honors `Retry-After` when supplied;
- no proxy rotation;
- no CAPTCHA handling;
- no browser-fingerprint or access-control evasion.

A marketplace may specify stricter limits in the actual permission. In that case, configure Fin Engine to the stricter limit.

### OLX

Default start page:

```text
https://www.olx.co.id/mobil-bekas_c198
```

### Mobil123

Default start page:

```text
https://www.mobil123.com/mobil-bekas-dijual
```

### Carmudi

Default start page:

```text
https://www.carmudi.co.id/mobil-bekas-dijual/indonesia
```

A narrower authorized search URL can be passed through `--start-url`.

## Authorized marketplace feed contract

The existing feed adapters remain available:

```text
olx_authorized_feed
mobil123_authorized_feed
carmudi_authorized_feed
```

These are preferred when the marketplace provides an API, export, or partner feed.

## Data minimization

The marketplace ingestion contract intentionally does not collect seller names, phone numbers, WhatsApp numbers, or other seller contact details.

Useful non-contact vehicle attributes such as mileage, transmission, fuel type, year, region, model and price may be retained.

## Other sources

### kemendagri_njkb_2025

Classification: `price_kind = "njkb"`.

NJKB is an official tax/reference value, not a marketplace asking price or transaction price.

### djp_vehicle_auction_limits

Classification: `price_kind = "auction_limit"`.

Auction limit is a reserve/floor-style signal, not a retail asking price or final transaction price.
