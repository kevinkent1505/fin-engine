# Business Dashboard

The Fin Engine business dashboard is a Next.js proof of concept for demonstrating vehicle collateral intelligence to product, strategy, sales, lenders, leasing companies, and design partners.

The dashboard is a presentation and workflow surface. It must not become a second analytics engine.

```text
marketplace / official sources
            ↓
Python ingestion + Neon
            ↓
Python analysis service
            ↓
Next.js server-side data adapter
            ↓
business dashboard
```

The TypeScript public API remains the external product API. For the POC, the dashboard talks to the internal Python analysis service server-side so the UI can demonstrate the actual analytical path without exposing internal endpoints or credentials in browser code.

## Code structure

```text
apps/dashboard/
├── app/
│   ├── layout.tsx
│   ├── globals.css
│   ├── page.tsx                  # Executive overview
│   ├── vehicle/page.tsx          # Vehicle Intelligence
│   ├── market/page.tsx           # Market Intelligence
│   └── methodology/page.tsx      # Data & Methodology
│
├── components/
│   ├── shell/
│   │   ├── dashboard-shell.tsx
│   │   └── dashboard-navigation.tsx
│   └── ui/
│       ├── analysis-status.tsx
│       ├── metric-card.tsx
│       └── source-badge.tsx
│
├── features/
│   ├── vehicle-intelligence/
│   │   ├── value-comparison-chart.tsx
│   │   └── price-history-chart.tsx
│   └── market-intelligence/
│       └── regional-market-chart.tsx
│
└── lib/
    ├── data/
    │   ├── analysis.ts           # server-side Python analysis client
    │   ├── index.ts              # dashboard data composition boundary
    │   └── poc.ts                # official context + explicit fallback fixture
    ├── format.ts
    └── types.ts
```

Use `components/ui` for generic presentation primitives. Domain-specific business visualizations belong in `features/<domain>`.

## Data path

Pages call:

```ts
const data = await getDashboardData();
```

`lib/data/index.ts` then requests the Python analysis service:

```text
POST /internal/v1/vehicles/valuation
```

The analysis service chooses its valuation source:

```text
DATABASE_URL configured
        ↓
latest listing observation per vehicle_record in PostgreSQL / Neon
        ↓
comparable_market_db_v1

DATABASE_URL not configured
        ↓
committed development comparable CSV
        ↓
comparable_market_v1
```

The dashboard labels these states separately:

```text
database     analysis engine + persisted marketplace observations
development  analysis engine + committed development comparables
fallback     analysis unavailable / no comparable result; explicit POC fixture
```

The fallback must never be silently represented as live analysis output.

## Why the database query uses latest observations

Crawler history is append-only, so one marketplace listing may have many observations across repeated runs. A current valuation snapshot must not overweight a listing just because it has been crawled more often.

The database-backed valuation therefore uses only the latest `listing` observation for each stable `vehicle_record` before calculating the comparable distribution.

## POC data policy

The dashboard now separates three categories of evidence.

**Analysis-engine asking-value signal:** comes from the Python service. It is marked `observed` when database-backed and `illustrative` when the service is using development comparables.

**Official public context:** BPS passenger-car counts and Kemendagri NJKB references remain official reference data.

**Still illustrative:** the auction/downside signal and fallback price history remain POC placeholders until those histories are exposed through the analysis API.

Regional Market Intelligence deliberately uses official BPS vehicle-stock data only; synthetic regional asking-price medians were removed from the POC.

Dashboard confidence labels are:

```text
official
observed
illustrative
```

## Current pages

### Executive Overview

Shows the current analysis-engine asking-value output, official NJKB reference, illustrative auction/downside signal, comparable range/count, regional BPS context, provenance, and a prominent analysis-status panel.

### Vehicle Intelligence

Shows the selected vehicle segment, analysis-engine valuation, comparable range, source status, signal comparison, and evidence registry.

When the analysis API exposes only a current snapshot, the chart displays one current point rather than fabricating historical observations.

### Market Intelligence

Uses official BPS vehicle-stock data for selected provinces. The POC does not invent regional asking prices. Future marketplace observations can add regional price/liquidity analytics after the data layer is populated.

### Data & Methodology

Explains signal definitions, source registry, confidence labels, current POC limitations, and validation boundaries.

## Floating glassmorphism navigation

The dashboard uses floating glass UI rather than a fixed solid sidebar.

Desktop:

```text
floating brand capsule   floating navigation capsule   POC status capsule
```

Mobile:

```text
floating brand/status at top
content
floating four-item bottom navigation above safe area
```

Shared CSS primitives:

```text
glass-panel      primary content cards
glass-subpanel   nested evidence/source blocks
glass-floating   navigation/status/brand chrome
action-primary   guaranteed high-contrast primary actions
action-secondary guaranteed high-contrast secondary actions
```

Glass is presentation only. Text and controls must remain readable without relying on backdrop blur or transparency.

## Responsive behavior

Build mobile-first.

Requirements include:

- 320 px minimum supported viewport;
- single-column content by default;
- 44 px or larger touch/navigation targets;
- floating bottom navigation on phones;
- safe-area padding for mobile browser/device insets;
- charts scroll inside their own focused container rather than causing page overflow;
- tables scroll locally when required;
- content remains usable at 200% browser zoom.

## Accessibility requirements

Current patterns include:

- skip-to-main-content link;
- semantic `main`, `nav`, `article`, `figure`, tables and captions;
- `aria-current="page"` on active navigation;
- strong active/inactive navigation contrast;
- visible keyboard focus rings;
- minimum touch-target sizing;
- chart `<title>` and `<desc>` plus screen-reader data tables;
- confidence states communicated by text, not color alone;
- `prefers-reduced-motion` handling;
- forced-colors/high-contrast fallback;
- primary/secondary action classes with opaque text/background contrast.

See [DASHBOARD_ACCESSIBILITY.md](./DASHBOARD_ACCESSIBILITY.md).

## Environment

Create `apps/dashboard/.env.local` from the example:

```bash
cp apps/dashboard/.env.example apps/dashboard/.env.local
```

Local defaults:

```text
ANALYSIS_BASE_URL=http://localhost:8001
DASHBOARD_VEHICLE_MAKE=Toyota
DASHBOARD_VEHICLE_MODEL=Avanza
DASHBOARD_VEHICLE_YEAR=2025
DASHBOARD_VEHICLE_REGION=DKI Jakarta
```

`ANALYSIS_BASE_URL` is server-side. Do not prefix it with `NEXT_PUBLIC_`.

## Running locally

Terminal 1:

```bash
cd apps/analysis
export VEHICLE_DATA_PATH="../../data/sample/vehicles.csv"
uv run uvicorn riil_analysis.main:app --reload --host 0.0.0.0 --port 8001
```

If `DATABASE_URL` is exported in that shell, the analysis endpoint uses PostgreSQL/Neon marketplace observations instead of the development CSV.

Terminal 2, from repository root:

```bash
yarn
yarn dev:dashboard
```

Open `http://localhost:3000`.

Validate before merging:

```bash
yarn typecheck:dashboard
yarn build:dashboard
cd apps/analysis && uv run pytest -v
```

## Next analytical integrations

The preferred sequence is:

```text
1. populate Neon with authorized marketplace observations
2. verify database-backed valuation in the Python analysis endpoint
3. expose persisted auction observations through analysis
4. expose true price-history series through analysis
5. add regional marketplace aggregation
6. add dashboard filters/search
7. move external customer workflows through stable TypeScript API contracts
```

## What does not belong in the dashboard

Do not place crawler implementations, normalization rules, SQL migrations, valuation formulas, underwriting decision rules, database credentials, or direct browser-to-Neon access inside `apps/dashboard`.

The dashboard consumes analytical outputs; it does not own analytical truth.
