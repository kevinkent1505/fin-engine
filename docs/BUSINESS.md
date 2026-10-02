# Fin Engine Business Overview

This document explains Fin Engine for business, product, strategy, sales, risk, and partnership stakeholders. It intentionally avoids implementation detail unless it affects how the product should be understood or sold.

## Executive summary

Fin Engine is a B2B vehicle-data and decision-support platform being developed under Riil.

Its purpose is to turn fragmented vehicle-market and official reference data into structured, traceable signals that can support decisions such as:

- collateral valuation;
- secured-lending and loan-to-value analysis;
- used-vehicle market benchmarking;
- recovery and downside analysis;
- portfolio monitoring;
- pricing and depreciation analysis;
- asset-risk and market-intelligence workflows.

Fin Engine is designed as a **decision-support data layer**. It is not intended to make an autonomous credit-approval decision or replace a lender's underwriting, KYC, AML, valuation, or risk-governance process.

## The business problem

Vehicle-finance decisions often depend on information that is spread across multiple places and expressed in different ways.

Examples include:

- marketplace asking prices;
- government reference values;
- auction limits;
- vehicle age and model information;
- regional price differences;
- listing persistence and price changes over time;
- future transaction or recovery data.

A single number labelled "vehicle price" can be misleading because each source represents a different economic signal.

Fin Engine preserves those distinctions, builds history around them, and makes the data easier to compare and consume.

## What Fin Engine does

At a business level, the platform follows this flow:

```text
vehicle data sources
        ↓
standardization + quality checks
        ↓
historical observation database
        ↓
analytical features
        ↓
API / data products
        ↓
customer decision workflows
```

The current development focus is vehicle collateral intelligence in Indonesia.

The longer-term design can extend to other collateral classes where reliable external data is available, such as property, commercial assets, heavy equipment, or other fixed assets.

## Who may use it

Potential B2B users include:

| Customer type | Example use |
| --- | --- |
| Banks | secured-lending collateral support and portfolio monitoring |
| Multifinance companies | used-car financing, LTV support and asset benchmarking |
| Leasing companies | asset valuation and depreciation monitoring |
| Used-car finance providers | comparable-market pricing and collateral checks |
| Marketplaces | pricing intelligence and market analytics |
| Insurers | asset-value and market-risk context |
| Valuation companies | external market/reference evidence |
| Risk and analytics teams | portfolio-level market and collateral signals |

These are target use cases, not claims that the current MVP already provides production-ready underwriting for every segment.

## Current data signals

Fin Engine deliberately keeps different value concepts separate.

| Signal | Meaning | Business interpretation |
| --- | --- | --- |
| `listing` | marketplace asking price | observable seller asking-price signal; not necessarily transaction value |
| `njkb` | official NJKB reference value | government reference/tax value; not a retail market price |
| `auction_limit` | published auction limit | downside/recovery-oriented reference signal; not the final auction sale price |
| `transaction` | future confirmed transaction price | intended for actual sale/transaction evidence when a reliable source is available |
| `reference` | generic reference signal | fallback category for a value that does not fit a stronger definition |

Keeping these signals separate is central to the product. Fin Engine should compare them, not silently treat them as interchangeable.

## Example business view

A future customer-facing vehicle view may look conceptually like this:

```text
Toyota Avanza 2023 — Jakarta

Official NJKB reference         Rp188m
Median marketplace asking       Rp218m
Observed asking-price range      Rp202m–236m
Published auction limit          Rp174m
Number of current comparables    37

Derived signals
Market / NJKB ratio              1.16x
Auction / market ratio           0.80x
Observed market liquidity        [future feature]
Depreciation trend               [future feature]
```

The numbers above are illustrative. They show how different source types may eventually be combined into one decision-support view while retaining their meaning and provenance.

## Potential products

Fin Engine can support several commercial delivery formats.

### 1. Vehicle valuation API

Customer sends a vehicle specification and receives market/reference signals.

Potential inputs:

```text
make
model
variant
year
region
mileage
```

Potential outputs:

```text
estimated market benchmark
range of comparable asking prices
sample size
NJKB reference
auction/recovery signals
confidence / data-quality information
```

### 2. Collateral intelligence API

A richer endpoint could provide features useful inside a lender's own underwriting model, such as:

```text
market-to-NJKB ratio
regional price variance
price dispersion
listing liquidity proxy
depreciation estimate
auction discount
observation recency
comparable count
```

The lender remains responsible for its final credit policy and decision.

### 3. Portfolio monitoring

A lender or leasing company could periodically submit or map a collateral portfolio and monitor changes in external market indicators.

Examples:

- market-value deterioration;
- unusually large regional price changes;
- declining liquidity;
- collateral segments with increasing downside risk.

### 4. Data feed / market intelligence

For customers that do not need a transactional API, Fin Engine could provide structured datasets or dashboards covering vehicle-market trends, depreciation, price ranges, and regional patterns.

### 5. Custom analytics

Larger customers may require institution-specific features, models, validation, or integration into existing underwriting and portfolio systems.

## Why historical observations matter

Fin Engine stores repeated observations rather than simply replacing yesterday's price with today's price.

For example:

```text
Listing ABC
1 Oct   Rp218m
8 Oct   Rp214m
15 Oct  Rp209m
```

Over time, this history can support signals that a one-time scraper cannot provide:

- price reductions;
- days observed on market;
- listing persistence;
- price volatility;
- seasonal changes;
- regional liquidity;
- model-level depreciation curves.

The historical dataset is therefore an important part of the long-term product value.

## Data provenance and trust

Every observation should remain traceable to its source and collection context.

Fin Engine records information such as:

- source;
- source record/listing identifier;
- source URL;
- observation time;
- signal type;
- crawl/import run;
- quality results;
- source-specific metadata;
- authorization reference for permission-gated marketplace crawling.

This matters because a B2B customer should be able to understand where a value came from and what it represents.

## Marketplace collection approach

Current marketplace integrations include authorized collection paths for OLX, Mobil123, and Carmudi.

The crawler is intentionally conservative:

- sequential requests;
- rate limiting;
- bounded crawl size;
- retry/backoff behavior;
- no CAPTCHA bypass;
- no proxy rotation for evasion;
- no access-control circumvention.

Marketplace permissions and any source-specific conditions should be preserved as part of source governance.

Seller names, phone numbers, WhatsApp numbers, and other seller contact details are not part of the intended analytical dataset.

## What the MVP already proves

The current codebase demonstrates the main technical building blocks needed for the product:

```text
✓ public API architecture
✓ Python analytical/data layer
✓ official NJKB ingestion
✓ official auction-limit ingestion
✓ authorized marketplace crawler framework
✓ marketplace feed ingestion
✓ data normalization and quality/audit reporting
✓ PostgreSQL historical persistence
✓ source-level record identity
✓ append-only observations
✓ development comparable-valuation flow
```

This should be understood as an engineering MVP, not yet a production-grade underwriting product.

## Important current limitations

The following limitations should be stated clearly in business discussions.

### Asking price is not transaction price

Marketplace data shows what sellers ask, not necessarily what buyers ultimately pay.

### Auction limit is not auction result

A published auction limit is useful as a downside/recovery reference but should not be described as the final realized sale value.

### NJKB is not market value

NJKB is an official reference value and should be compared with, not substituted for, observed market evidence.

### Cross-source vehicle identity is not solved yet

Fin Engine currently knows that two records may describe similar vehicles, but it does not yet claim that records across different sources refer to the exact same physical vehicle.

### Current valuation is still an MVP

The first comparable-market method is intentionally simple. Production valuation will require stronger comparable selection, model/variant resolution, mileage and condition adjustments, geographic treatment, evaluation against reliable outcomes, and confidence calibration.

### Fin Engine is not a credit bureau or autonomous lender

The product should support customer decisions rather than make unsupervised credit decisions on behalf of a financial institution.

## Commercial model options

Potential monetization models include:

| Model | Description |
| --- | --- |
| API subscription | recurring fee with usage allowance |
| Usage-based API | charge per lookup / valuation / feature request |
| Data feed | recurring delivery of structured market datasets |
| Dashboard | subscription market-intelligence product |
| Custom analytics | institution-specific analysis, model or integration work |
| Enterprise contract | negotiated access, SLA, data coverage and support |

Pricing has not yet been finalized and should be validated with design partners.

## Go-to-market approach

A practical initial commercial path is to work with a small number of design partners rather than trying to launch a broad generic product immediately.

A design-partner engagement can answer:

1. Which collateral decisions are most painful today?
2. Which data fields are actually used in the credit or valuation workflow?
3. How much improvement comes from market data versus existing internal data?
4. What level of data freshness and coverage is necessary?
5. Which outputs need explanation or auditability?
6. How should the API integrate with the customer's existing decision engine?

The initial target should be proving measurable decision value, not maximizing the number of data sources.

## Product roadmap

The roadmap is directional and should evolve with customer validation.

### Phase 1 — Data foundation

Current focus:

- official reference data;
- authorized marketplace data;
- auction signals;
- normalization;
- quality controls;
- historical storage;
- source provenance.

### Phase 2 — Market intelligence

Planned analytical features:

- stronger comparable selection;
- model/variant entity resolution;
- price distributions;
- regional adjustments;
- mileage adjustments;
- depreciation curves;
- listing liquidity;
- price-change history.

### Phase 3 — Collateral intelligence

Potential outputs:

- estimated collateral market value;
- confidence range;
- downside/recovery indicators;
- market-to-reference ratios;
- volatility and liquidity features;
- portfolio monitoring signals.

### Phase 4 — Customer-specific decision support

Potential enterprise extensions:

- customer-specific models;
- integration with internal loan/performance data;
- customized risk features;
- model monitoring and validation;
- broader collateral classes.

### Phase 5 — Riil first-party data

If the Riil B2C product later generates consented, privacy-governed first-party financial or asset data, that may become an additional source of decision intelligence.

That integration is future-facing and should remain separated from the current external-data platform until governance, consent, security, and product requirements are defined.

## Long-term differentiation

The defensible value of Fin Engine is not simply "having a scraper."

Potential differentiation comes from the combination of:

```text
historical observations
+ normalization
+ entity resolution
+ source provenance
+ quality controls
+ derived features
+ customer integration
+ future first-party Riil signals
```

Scraping is one acquisition method. The product is the structured, trusted intelligence layer built on top of the data.

## Business terminology

| Term | Plain-language meaning |
| --- | --- |
| Comparable | a similar vehicle used as market evidence |
| Observation | one recorded value for a source record at a point in time |
| Provenance | where the data came from and how/when it was collected |
| Listing liquidity | proxy for how easily/quickly a vehicle type appears to sell or leave the market |
| Depreciation | change in asset value as it ages or market conditions change |
| LTV | loan-to-value ratio; loan amount relative to collateral value |
| Collateral intelligence | external data and derived signals that help assess the value and risk of pledged assets |
| Decision support | information used by a customer's own people, policy, or models to make a decision |

## Related documentation

For implementation detail, see:

- [Developer Documentation](./README.md)
- [Architecture](./ARCHITECTURE.md)
- [Source Registry](./SOURCES.md)
- [Database](./DATABASE.md)
- [Deployment](./DEPLOYMENT.md)
