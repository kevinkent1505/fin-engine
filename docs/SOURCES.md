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

The following sources are **not enabled as automated Fin Engine adapters**:

- OLX Indonesia;
- Mobil123;
- Carmudi.

Their currently published terms restrict automated scraping/crawling and/or commercial aggregation of listing content and prices without permission. Fin Engine should only integrate those sources through an approved/licensed feed, API, partnership, or explicit written permission.

## kemendagri_njkb_2025

**Source ID:** `kemendagri_njkb_2025`

**Publisher:** Kementerian Dalam Negeri Republik Indonesia

**Document:** Permendagri No. 7 Tahun 2025 tentang Dasar Pengenaan Pajak Kendaraan Bermotor, Bea Balik Nama Kendaraan Bermotor, dan Pajak Alat Berat Tahun 2025

**Provenance page:**  
https://peraturan.bpk.go.id/Details/321612/permendagri-no-7-tahun-2025

**Acquisition:** Official PDF exposed through JDIH BPK.

**Classification:** `price_kind = "njkb"`

**Important limitation:** NJKB is an official tax/reference value. It is not a live marketplace listing price or confirmed transaction price.

## djp_vehicle_auction_limits

**Source ID:** `djp_vehicle_auction_limits`

**Publisher:** Direktorat Jenderal Pajak, Kementerian Keuangan Republik Indonesia

**Discovery page:**  
https://www.pajak.go.id/info-lelang-page/

**Acquisition:** low-frequency retrieval of public official auction announcements that clearly identify a single vehicle and publish a numeric auction limit.

**Classification:** `price_kind = "auction_limit"`

**Fields captured where available:**

- make and vehicle descriptor;
- production year;
- auction limit;
- deposit;
- mileage;
- auction date text;
- auction location text;
- announcement URL and title.

**Important limitation:** the auction limit is a reserve/floor-style auction signal. It is neither a retail asking price nor the final transaction price. It may be useful for recovery/downside analysis, but it must not be silently treated as a marketplace comparable.

The first implementation deliberately caps network requests during development and skips announcements that cannot be mapped to a single vehicle with a make, year, type and numeric auction limit.

## Future market-listing sources

The preferred path for commercial marketplace data is an approved/licensed API, feed, partnership, or source with clearly compatible automated-access and reuse terms. Such adapters should emit `price_kind = "listing"` and preserve source-specific provenance.
