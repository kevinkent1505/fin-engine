# Riil → Fin Engine: Phase 1 public-market import

**Status:** implemented adapter and tests; production import is opt-in and has not been run automatically.

## Scope and independence

This is a read-only integration in the **Fin Engine** repository. Riil continues to
publish its public financial-market artifact and function on Cloudflare Pages
independently. Fin Engine can ingest that artifact as one optional source,
alongside its native official/authorized data sources. No changes to the Riil
repository, its D1 database, analytics endpoints, calculator engines, article
builder or CMS are necessary.

Only `https://riil.id/data/market-snapshot.json` is fetched by the default
command; an existing saved copy may be supplied with `--input-file`. The
importer does not follow redirects, query Riil's private GitHub repository, or
copy any raw JSON keys except explicitly approved market-indicator fields.

Imported indicators: `usd_idr`, `inflation_yoy`, `oil_icp`, `ihsg`,
`ihsg_previous`, Antam gold price/buyback, and six named fuel prices.
The currently published snapshot produces **13 indicator observations**.

All records carry Riil's snapshot origin, original cited source, source date,
unit and semantic revision hash. `Riil` is **not** relabeled as the official
original publisher, and Fin Engine does **not** claim these values were
independently verified. The data are retained for internal integration
evaluation only until original source terms and downstream redistribution
rights have been checked.

Riil's `data/market-rates.json` (including BI-Rate and the thin one-bank SBDK
sample) is **not** part of this initial importer. Neither is Riil's tracking,
D1, personal financial input, account or saved-calculation data.

## Get started on Windows / Git Bash

From the Fin Engine repository root:

```bash
git switch feature/marketplace-poc
git pull --ff-only origin feature/marketplace-poc
yarn test:analysis
yarn env:check
```

**Preview (no database write):**

```bash
yarn import:riil-market
```

This fetches Riil's published market snapshot. If the site is unavailable,
copy the **existing published JSON** to
`fin-engine/data/generated/riil-market-snapshot.json`, then preview the
saved file with:

```bash
yarn import:riil-market \
  --input-file ../../data/generated/riil-market-snapshot.json \
  --output ../../data/generated/riil-market-preview.json
```

Important: file arguments are relative to `apps/analysis`, where the
Python process runs. The preview contains market figures and source
citations only. It does not connect to Neon.

**Persist after reviewing your preview:**

```bash
yarn migrate upgrade head
yarn import:riil-market --persist-db
```

Or persist an approved local snapshot:

```bash
yarn import:riil-market \
  --input-file ../../data/generated/riil-market-snapshot.json --persist-db
```

`DATABASE_URL` loads from the root Git-ignored `.env.local` automatically.
The migration `0003_market_indicators.py` creates a separate
`market_indicator_observations` table; existing vehicle tables remain
unchanged. The importer also creates an `ingestion_runs` audit record
when it inserts new observations.

**Replay safety:** identical source indicator+date+semantic revision is
skipped and does not create another ingestion run. Corrected figures for
the same reference date are appended as new revisions rather than overwriting
history. Invalid or incomplete JSON is rejected before database writes.

## Verification

Inspect the database after a successful import:

```sql
SELECT source_key, indicator_code, as_of, value, unit,
       original_publisher
FROM market_indicator_observations
WHERE source_key = 'riil_published_market_snapshot_v1'
ORDER BY indicator_code, as_of DESC;
```

Then re-run the same `yarn import:riil-market --persist-db`; it should
report `inserted_observations: 0` and `skipped_existing: 13` if Riil's
published values have not changed.

Run `yarn test:analysis` to test field allowlisting, incorrect dates, invalid
units/source URLs, deduplication, append-only correction revisions and a
file-based dry-run without `DATABASE_URL`.

## What's deliberately not implemented yet

- No automatic scheduled job, new public indicator API, dashboard charts or
  Fin Engine → Riil return feed.
- No Riil-side exporter or modification to Riil's publishing workflow.
- No private, personal, behavioral, or analytics data handoff.
- No direct Neon/D1 access across products.
- No permission to redistribute external cited publisher data commercially.

The next engineering gate is to independently verify the real published
snapshot and deploy a separately scheduled, monitored Fin Engine import job
with freshness reporting. Failures must leave previous validated observations
available, and an unavailable Riil feed must not interrupt either product.

See [the integration roadmap](./RIIL_INTEGRATION_ROADMAP.md) and
[the inbound JSON contract](../contracts/inbound/riil-market-snapshot.v1.schema.json).
