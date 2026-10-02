# Business Dashboard

The Fin Engine business dashboard is a Next.js proof of concept for demonstrating vehicle collateral intelligence to product, strategy, sales, lenders, leasing companies and design partners.

The dashboard is intentionally separate from the public API and Python analysis service:

```text
apps/
├── api/          TypeScript / Fastify public API
├── analysis/     Python ingestion, normalization, persistence and analytics
└── dashboard/    Next.js business-facing POC
```

## Why a separate app

The dashboard is a presentation and workflow surface. It should not become a second analytics engine.

Keep these boundaries:

```text
Python analysis / persisted data
            ↓
TypeScript API or server-side query layer
            ↓
Next.js dashboard
            ↓
business user
```

Do not duplicate valuation formulas, source normalization rules or crawler logic inside the dashboard.

## Recommended dashboard code structure

```text
apps/dashboard/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  # Executive overview
│   ├── vehicle/
│   │   └── page.tsx              # Vehicle Intelligence
│   ├── market/
│   │   └── page.tsx              # Market Intelligence
│   └── methodology/
│       └── page.tsx              # Data & Methodology
│
├── components/
│   ├── shell/
│   │   └── dashboard-shell.tsx   # navigation / app chrome
│   └── ui/
│       ├── metric-card.tsx       # reusable business UI primitive
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
    │   ├── index.ts              # server-side data-access boundary
    │   └── poc.ts                # deterministic POC fixtures
    ├── format.ts
    └── types.ts
```

This is intentionally feature-oriented rather than putting every component in one global directory.

Use `components/ui` only for generic primitives that have no Fin Engine domain meaning. Put domain-specific visualizations and workflow components inside `features/<domain>`.

## Data-access rule

Pages should not know whether their data came from:

- a fixture;
- Neon PostgreSQL;
- the Fin Engine TypeScript API;
- a future analytics endpoint.

Pages call the data layer:

```ts
const data = await getDashboardData();
```

The POC implementation currently resolves that call from:

```text
lib/data/poc.ts
```

Later, replace the internals of `lib/data/index.ts` rather than rewriting the routes.

Target evolution:

```text
POC fixture
   ↓
lib/data/index.ts
   ↓
Next.js pages
```

becomes:

```text
Neon / Fin Engine API
          ↓
lib/data/index.ts
          ↓
Next.js pages
```

## POC data policy

The dashboard currently combines two classes of data.

### Official public references

The POC includes public official references such as:

- BPS passenger-car counts by province;
- Kemendagri NJKB reference values.

These are marked `official` in the UI.

### Illustrative business signals

Until repeated marketplace and auction observations are connected to the query layer, the dashboard uses clearly marked illustrative fixtures for:

- marketplace asking-price median;
- asking-price range;
- asking-price history;
- regional asking-price medians;
- auction/downside reference.

These values are marked `illustrative` and must not be represented externally as live evidence.

The UI intentionally exposes this distinction.

## Data confidence model

Dashboard data has one of three confidence labels:

```text
official
observed
illustrative
```

Meaning:

| Label | Meaning |
| --- | --- |
| `official` | sourced from an official public reference and traceable to its publication |
| `observed` | collected by Fin Engine from an authorized live or licensed source |
| `illustrative` | POC fixture used to demonstrate product behavior only |

Do not silently promote an illustrative value to observed or official.

## Current dashboard pages

### Executive Overview

Answers the business question:

> What is the collateral-intelligence story at a glance?

Shows:

- indicative asking-price median;
- official NJKB;
- market/NJKB relationship;
- auction/asking relationship;
- selected vehicle;
- regional passenger-car stock;
- visible data provenance.

### Vehicle Intelligence

Answers:

> What evidence do we have about this specific vehicle segment?

Shows:

- vehicle / variant / year / region;
- asking-price signal;
- NJKB reference;
- downside signal;
- observed range;
- price-history visualization;
- source evidence.

### Market Intelligence

Answers:

> How does regional market context change the collateral picture?

Shows:

- BPS passenger-car stock;
- selected regional coverage;
- regional comparison table;
- future market-depth, liquidity and portfolio-monitoring concepts.

### Data & Methodology

Answers:

> What does each number mean and where did it come from?

Shows:

- signal definitions;
- source registry;
- confidence labels;
- POC limitations;
- next validation steps.

## Visualization approach

The dashboard uses D3 for domain-specific SVG charts and Tailwind for layout/styling.

Use D3 primarily for:

- scales;
- axes;
- line / area generators;
- distributions;
- more specialized analytical visualizations later.

Do not use D3 to manually control the entire DOM. Let React own rendering and use D3 for mathematical/visualization primitives.

Current pattern:

```tsx
const x = scaleLinear().domain(domain).range(range);

return (
  <svg>
    {data.map((item) => (
      <circle cx={x(item.value)} ... />
    ))}
  </svg>
);
```

This keeps charts compatible with React composition and Next.js.

## Styling

Tailwind CSS is the dashboard styling framework.

The visual language is intentionally business-oriented:

- neutral white/slate surfaces;
- blue as the primary analytical accent;
- green for official/reference-positive context;
- amber for caution / illustrative / downside context;
- restrained charts;
- dense but readable information hierarchy;
- visible source confidence.

Avoid decorative dashboard elements that do not communicate a business decision or data-quality signal.

## Running locally

From the repository root:

```bash
yarn
yarn dev:dashboard
```

Open:

```text
http://localhost:3000
```

If port 3000 is already in use, Next.js may select another port.

Build/typecheck:

```bash
yarn typecheck:dashboard
yarn build:dashboard
```

## Public-reference values currently used

The POC fixture currently includes selected BPS 2023 passenger-car counts for:

- Jawa Timur;
- Jawa Barat;
- DKI Jakarta;
- Jawa Tengah;
- Banten;
- Sumatera Utara;
- Bali.

It also uses the 2025 official NJKB of `Rp214,000,000` for Toyota Avanza 1.5 Veloz M/T, production year 2025, from Permendagri No. 7 Tahun 2025.

Source URLs are visible in the Data & Methodology page.

## Migration to live Fin Engine data

The recommended sequence is:

```text
1. keep dashboard UI stable
2. persist authorized marketplace observations in Neon
3. persist/verify official auction observations
4. add server-side dashboard queries
5. replace fixture implementation inside lib/data/index.ts
6. retain confidence/provenance metadata
7. add filtering and search only after the data layer is stable
```

For the first live implementation, prefer server-side reads from an internal API or a read-only database access layer. Do not expose Neon credentials to browser-side code.

## Suggested live dashboard query contracts

A future internal dashboard API could expose:

```text
GET /internal/dashboard/overview
GET /internal/dashboard/vehicles/search
GET /internal/dashboard/vehicles/:key
GET /internal/dashboard/markets/regions
GET /internal/dashboard/sources
```

These are not public API contracts yet and should not be added until the underlying analytical definitions are stable.

## What not to put in the dashboard

Do not put these directly in `apps/dashboard`:

- crawler implementations;
- normalization logic;
- source-specific scraping rules;
- valuation formulas;
- underwriting decision rules;
- database migrations;
- direct client-side database credentials.

The dashboard consumes domain outputs; it does not own them.

## POC success criteria

The dashboard is successful when a non-technical B2B stakeholder can understand, within a few minutes:

1. what vehicle segment is being analyzed;
2. how market, official-reference and downside signals differ;
3. what the source evidence is;
4. how regional context could support collateral decisions;
5. which values are real official data versus illustrative POC content;
6. what additional value Fin Engine gains once repeated live observations are available.
