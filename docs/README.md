# Fin Engine Documentation

Use this directory for detailed business, developer, and operator documentation. The repository root README is the concise entry point.

## Documentation map

| Document | Use it for |
| --- | --- |
| [BUSINESS.md](./BUSINESS.md) | business overview, customer use cases, data-signal meaning, product limitations, commercial model and roadmap |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | local setup, environment variables, running services, common commands and troubleshooting |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | system boundaries, TypeScript/Python ownership, data flows and design principles |
| [INGESTION.md](./INGESTION.md) | source adapters, raw/canonical contracts, crawler behavior, quality and adding new sources |
| [SOURCES.md](./SOURCES.md) | source registry, access/provenance rules and source-specific interpretation |
| [DATABASE.md](./DATABASE.md) | Neon/PostgreSQL schema, migrations, persistence behavior and useful SQL |
| [TESTING.md](./TESTING.md) | test layers, regression expectations, live smoke tests and pre-merge checks |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Cloud Run Jobs target architecture, secrets, rollout and scheduler strategy |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | contribution workflow and change checklists |

## Start here

Business, product, strategy, sales or partnership stakeholder:

```text
README.md
  ↓
BUSINESS.md
  ↓
SOURCES.md if deeper data-source context is needed
```

New developer:

```text
README.md
  ↓
DEVELOPMENT.md
  ↓
ARCHITECTURE.md
  ↓
relevant specialist guide
```

Working on a crawler/source:

```text
ARCHITECTURE.md
INGESTION.md
SOURCES.md
TESTING.md
```

Working on persistence:

```text
ARCHITECTURE.md
DATABASE.md
TESTING.md
```

Working on deployment:

```text
DEVELOPMENT.md
DATABASE.md
DEPLOYMENT.md
```

Working on the public API:

```text
ARCHITECTURE.md
DEVELOPMENT.md
TESTING.md
Bruno collection
```

## Documentation rule

If a code change alters a business-facing product capability, developer-facing contract, deployment assumption, source semantic, CLI flag, environment variable, schema, or public API, update the relevant documentation in the same change set.

Keep the root README short enough that a new stakeholder can understand the project and get to the correct detailed guide quickly.