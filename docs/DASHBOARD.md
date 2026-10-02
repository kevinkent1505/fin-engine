# Business Dashboard

The Fin Engine business dashboard is a Next.js proof of concept for demonstrating vehicle collateral intelligence to product, strategy, sales, lenders, leasing companies, and design partners.

The dashboard is intentionally separate from the public API and Python analysis service:

```text
apps/
├── api/          TypeScript / Fastify public API
├── analysis/     Python ingestion, normalization, persistence and analytics
└── dashboard/    Next.js business-facing POC
```

The dashboard is a presentation and workflow surface. It must not become a second analytics engine.

```text
Python analysis / persisted data
            ↓
TypeScript API or server-side query layer
            ↓
Next.js dashboard
            ↓
business user
```

Do not duplicate valuation formulas, source normalization rules, crawler logic, or underwriting rules inside the dashboard.

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
    │   ├── index.ts              # server-side data-access boundary
    │   └── poc.ts                # deterministic POC fixtures
    ├── format.ts
    └── types.ts
```

Use `components/ui` only for generic presentation primitives. Domain-specific business visualizations belong in `features/<domain>`.

## Data-access boundary

Pages should not know whether their data came from a fixture, Neon PostgreSQL, the Fin Engine API, or a future analytics endpoint.

Pages call:

```ts
const data = await getDashboardData();
```

The POC currently resolves that call from `lib/data/poc.ts`.

Later, replace the implementation behind `lib/data/index.ts` rather than rewriting the routes:

```text
POC fixture                Neon / Fin Engine API
    ↓                              ↓
lib/data/index.ts    →      lib/data/index.ts
    ↓                              ↓
Next.js pages               same Next.js pages
```

Do not expose Neon credentials to browser-side code.

## Current pages

### Executive Overview

Answers: **What is the collateral-intelligence story at a glance?**

Shows indicative asking price, official NJKB, market/NJKB relationship, auction/asking relationship, selected vehicle, regional passenger-car stock, and visible provenance.

### Vehicle Intelligence

Answers: **What evidence do we have about this specific vehicle segment?**

Shows vehicle/variant/year/region, asking-price signal, NJKB reference, downside signal, observed range, price-history visualization, and source evidence.

### Market Intelligence

Answers: **How does regional market context change the collateral picture?**

Shows BPS passenger-car stock, selected regional coverage, regional comparison, and future market-depth/liquidity/portfolio-monitoring concepts.

### Data & Methodology

Answers: **What does each number mean and where did it come from?**

Shows signal definitions, source registry, confidence labels, POC limitations, and validation steps.

## POC data policy

The dashboard currently combines official public references with clearly marked illustrative business signals.

Official examples include BPS passenger-car counts and Kemendagri NJKB values.

Illustrative POC values currently include marketplace asking-price median/range/history, regional asking-price medians, and auction/downside values until repeated live observations are connected to the query layer.

Dashboard confidence labels are:

```text
official
observed
illustrative
```

Do not silently promote an illustrative value to observed or official.

## Visualization approach

The dashboard uses D3 for visualization mathematics and React for rendering.

Use D3 primarily for scales, lines/areas, axes, distributions, and specialized analytical geometry. Do not have D3 manually own the React DOM.

Each chart should follow this accessibility pattern:

```text
figure / figcaption
      ↓
responsive SVG
      ↓
<title> + <desc>
      ↓
visible labels
      ↓
screen-reader data table
```

On narrow screens, charts may scroll horizontally inside their own focusable region. Do not create page-level horizontal overflow just to preserve a chart's minimum readable width.

## Glassmorphism design system

The dashboard now uses an accessible glassmorphism visual language.

Shared CSS primitives:

```text
glass-panel      primary cards / visualizations
glass-subpanel   nested evidence / source blocks
glass-header     sticky dashboard header
```

The design combines translucent light surfaces, subtle borders, background blur, soft shadows, and strong slate text. Glass should remain a presentation effect; never reduce opacity so far that underlying gradients or content interfere with reading.

Desktop uses a dark translucent sidebar. Mobile/tablet uses a sticky glass header with horizontally scrollable pill navigation.

Tailwind remains the layout/component utility framework. Global glass, accessibility, and progressive-enhancement rules live in `app/globals.css`.

## Responsive behavior

Build mobile-first.

Current rules include:

- 320 px minimum supported page width;
- single-column content by default;
- two/four-column metric layouts only as space becomes available;
- desktop sidebar at `lg` and above;
- mobile navigation below `lg`;
- 44 px minimum navigation/touch targets;
- smaller phone heading/card padding with larger desktop spacing;
- horizontally scrollable wide charts and tables;
- no fixed page-level desktop content width beyond the centered maximum container.

See [DASHBOARD_ACCESSIBILITY.md](./DASHBOARD_ACCESSIBILITY.md) for the complete responsive and accessibility requirements.

## Accessibility rules

Accessibility is a dashboard requirement, not a later polish pass.

Current implementation includes:

- skip-to-main-content link;
- semantic `main`, `nav`, `article`, `figure`, and table structures;
- `aria-current="page"` for active navigation;
- visible `:focus-visible` treatment;
- keyboard-focusable scroll regions;
- chart titles/descriptions and non-visual data tables;
- table captions and row/column heading scopes;
- textual confidence/status labels so color is supplementary;
- `prefers-reduced-motion` support;
- forced-colors/high-contrast fallback;
- stronger text/chart contrast than the initial POC.

Do not remove any of these patterns when restyling a component.

## Running locally

From the repository root:

```bash
yarn
yarn dev:dashboard
```

Open `http://localhost:3000`.

Validate before merging:

```bash
yarn typecheck:dashboard
yarn build:dashboard
```

Also manually test phone widths, keyboard navigation, 200% browser zoom, reduced-motion mode, and high-contrast/forced-colors behavior.

## Migration to live Fin Engine data

Recommended sequence:

```text
1. keep dashboard UI stable
2. persist authorized marketplace observations in Neon
3. persist/verify official auction observations
4. add server-side dashboard queries
5. replace fixture implementation inside lib/data/index.ts
6. retain confidence/provenance metadata
7. add filtering/search after the live data layer is stable
```

A future internal dashboard API could expose overview, vehicle-search/detail, regional-market, and source-registry contracts. These are not public API contracts yet.

## What does not belong in the dashboard

Do not put crawler implementations, normalization logic, source-specific scraping rules, valuation formulas, underwriting decision rules, database migrations, or client-side database credentials in `apps/dashboard`.

The dashboard consumes domain outputs; it does not own them.

## POC success criteria

The dashboard is successful when a non-technical B2B stakeholder can understand within a few minutes:

1. what vehicle segment is being analyzed;
2. how asking-price, official-reference, and downside signals differ;
3. what the source evidence is;
4. how regional context could support collateral decisions;
5. which values are official/observed versus illustrative POC content;
6. what additional value repeated live observations would provide;
7. the same story on desktop, tablet, and phone, including keyboard and assistive-technology access.
