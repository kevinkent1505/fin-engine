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

## kemendagri_njkb_2025

**Source ID:** `kemendagri_njkb_2025`

**Publisher:** Kementerian Dalam Negeri Republik Indonesia

**Document:** Permendagri No. 7 Tahun 2025 tentang Dasar Pengenaan Pajak Kendaraan Bermotor, Bea Balik Nama Kendaraan Bermotor, dan Pajak Alat Berat Tahun 2025

**Provenance page:**  
https://peraturan.bpk.go.id/Details/321612/permendagri-no-7-tahun-2025

**Acquisition:** Official PDF exposed through JDIH BPK.

**Data used:** vehicle make, official type, production year, NJKB, weight and DP PKB where present.

**Classification:** official reference value.

**Important limitation:** NJKB is not a live marketplace listing price or confirmed transaction price. Downstream code keeps `price_kind = "njkb"` so it cannot silently become market-listing evidence.

This is the first integration because it is an official public reference document and is useful for testing the ingestion pipeline against real vehicle-value records. Commercial product use should still undergo the project's source/legal review rather than assuming all public web content has unrestricted reuse rights.

## Future market-listing sources

Marketplace adapters should not be added until their automated-access and commercial-reuse conditions have been reviewed. When added, they should emit `price_kind = "listing"` and preserve source-specific provenance.
