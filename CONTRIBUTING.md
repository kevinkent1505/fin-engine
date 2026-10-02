# Contributing to Fin Engine

This repository is still early-stage, so contribution discipline matters more than process complexity.

## Before changing code

Read:

- [Architecture](./docs/ARCHITECTURE.md)
- [Local development](./docs/DEVELOPMENT.md)
- [Ingestion](./docs/INGESTION.md) for source work
- [Database](./docs/DATABASE.md) for persistence/schema work
- [Testing](./docs/TESTING.md)

## Core ownership rule

TypeScript owns public API/product concerns.

Python owns data acquisition, normalization, quality, persistence and analytical domain logic.

Do not duplicate analytical logic across both languages.

## Branch and change scope

Prefer small, reviewable changes with one clear purpose.

Examples:

```text
feat: add source adapter
fix: reject malformed source rows
feat: add valuation feature
chore: add migration
refactor: isolate parser logic
docs: update ingestion guide
```

Avoid mixing a large parser rewrite, database migration and unrelated API redesign in one change unless they are inseparable.

## Python workflow

```bash
cd apps/analysis
uv sync --extra dev
uv run pytest -v
```

Keep Python 3.12 compatibility because production containers currently use Python 3.12.

## TypeScript workflow

From the repository root:

```bash
yarn
yarn typecheck:api
yarn build:api
```

For local development:

```bash
yarn dev:api
```

## Public API changes

Every public API route or contract change must update Bruno in the same development pass.

Checklist:

```text
[ ] implementation updated
[ ] validation updated
[ ] public contract updated if applicable
[ ] Bruno request updated
[ ] Bruno assertions updated
[ ] error paths checked
[ ] typecheck/build pass
```

Do not add Bruno requests for internal CLI-only ingestion behavior unless it becomes an HTTP interface.

## Ingestion changes

A new or changed source adapter should preserve:

```text
source identity
source record identity
source URL
observed_at
price_kind
raw/source metadata
```

Every source must explicitly represent what its numeric value means.

Do not treat these as interchangeable:

```text
listing
njkb
auction_limit
transaction
reference
```

For authorized marketplace crawlers:

- use the shared polite HTTP behavior;
- preserve sequential execution unless explicitly redesigned and approved;
- do not lower the hard one-second request-delay floor;
- do not add proxy rotation, CAPTCHA bypass or access-control evasion;
- keep the authorization reference in provenance;
- exclude seller contact details from the canonical ingestion contract.

See [INGESTION.md](./docs/INGESTION.md).

## Database changes

Never change SQLAlchemy models without considering migrations.

A persistent schema change should usually include:

```text
SQLAlchemy model
Alembic migration
persistence/query changes
tests
documentation
```

Do not use `create_all()` as a substitute for production migrations.

See [DATABASE.md](./docs/DATABASE.md).

## Testing expectations

Do not make normal unit tests depend on live marketplaces or government sites.

Use deterministic fixtures for:

- HTML;
- JSON-LD;
- CSV feeds;
- PDF-table rows;
- malformed edge cases.

A production parser bug should get a regression fixture/test before the fix is considered complete.

See [TESTING.md](./docs/TESTING.md).

## Documentation expectations

Update documentation when changing:

- source semantics;
- source IDs;
- CLI arguments;
- environment variables;
- database schema;
- deployment assumptions;
- public API behavior;
- architectural boundaries.

The README should remain a concise entry point. Put detailed operational/developer material in `docs/`.

## Security and secrets

Never commit:

```text
DATABASE_URL credentials
API keys
marketplace credentials
private permission documents
secret-manager values
```

Use environment variables locally and secret managers in cloud deployments.

Authorization references stored in records should be identifiers/references, not passwords or sensitive contract contents.

## Data integrity principles

1. Preserve provenance.
2. Prefer append-only history for observations.
3. Do not fabricate missing source values.
4. Flag semantic uncertainty rather than hiding it.
5. Keep raw/source meaning separate from derived analytical meaning.
6. Do not claim cross-source vehicle identity until entity resolution exists.

## Review checklist

Before considering a change complete:

```text
[ ] code follows TypeScript/Python responsibility boundary
[ ] tests pass
[ ] new parser cases have fixtures
[ ] public API changes include Bruno updates
[ ] schema changes include migrations
[ ] provenance is preserved
[ ] price_kind semantics are correct
[ ] docs are updated
[ ] no secrets are committed
```
