# Local Development

This guide is the fastest path from a fresh clone to a working Fin Engine development environment.

## Prerequisites

- Git
- Node.js 20+
- Yarn 1.22.x
- Python 3.12+
- Standard Python `venv` and `pip` (bundled with Python; no uv required)
- Docker Desktop or another Docker Compose-compatible runtime, optional
- Neon/PostgreSQL when testing database-backed valuation/persistence

The repository currently contains three application surfaces:

```text
apps/api        TypeScript / Fastify public API
apps/analysis   Python / FastAPI, ingestion, normalization, persistence, valuation
apps/dashboard  Next.js / Tailwind / D3 business dashboard POC
```

## Clone and bootstrap

```bash
git clone https://github.com/kevinkent1505/fin-engine.git
cd fin-engine
yarn

yarn setup
```

The same commands work from PowerShell, Windows Terminal, Git Bash, macOS Terminal, and Linux. If the Python executable is not on PATH, set `FIN_ENGINE_PYTHON` to its full path before running `yarn setup`. Python 3.11 is not supported; install Python 3.12+ separately. Existing `apps/analysis/.venv` environments are reused if compatible. If your `.venv` was made by Python 3.11 or another operating system, delete **only** the local `apps/analysis/.venv` directory and rerun `yarn setup`.

The launcher uses Node.js rather than Bash/PowerShell to manage processes, and invokes `.venv`'s Python executable directly without shell activation. The first setup requires network access to install Python packages using pip; Python itself must already be installed.

## Environment variables

### Project-local `.env.local` (recommended)

Create a file named `.env.local` **at the repository root**, next to
`package.json`, or copy the safe template:

```bash
cp .env.local.example .env.local
```

Then insert your actual Neon database connection string into
`fin-engine/.env.local`:

```dotenv
DATABASE_URL="postgresql://USER:PASSWORD@HOST/neondb?sslmode=require"
ANALYSIS_BASE_URL=http://localhost:8001
```

The `yarn dev`, `yarn dev:analysis`, `yarn dev:api`,
`yarn dev:dashboard`, `yarn refresh:bps`, `yarn refresh:njkb`,
`yarn refresh:official`, `yarn refresh:data`, `yarn ingest`, `yarn migrate`, and Python
test commands load the root `.env.local` automatically via the Node launcher.
This works on Windows (Git Bash or PowerShell), macOS, and Linux without
manual shell exports, `uv`, or an extra npm package.

Check configuration status **without printing your password**:

```bash
yarn env:check
```

**Precedence:** Existing environment variables (including permanent Windows
user variables or values exported in the current terminal) override
`.env.local`. If you want the file's `DATABASE_URL` to take effect, unset
the old value in that shell (`unset DATABASE_URL` in Git Bash) or remove
your old permanent Windows user variable and reopen the terminal.
Missing keys fall back to existing launcher defaults. Restart running
services after editing `.env.local`.

The loader reads values as text; no command substitution or shell execution
occurs. Use quotes for values with spaces, comments, or special characters.
The root `.env.local` file is Git-ignored. Keep it private: it contains
plaintext credentials, and avoid copying or pasting its contents into
issue reports or logs. Docker and cloud deployments use their own
environment/secret configuration, not this local file.

Do not commit real credentials.

| Variable | Used by | Purpose |
| --- | --- | --- |
| `ANALYSIS_BASE_URL` | TypeScript API + dashboard server | Python analysis-service URL |
| `VEHICLE_DATA_PATH` | Python analysis | Development comparable CSV when no DB is configured |
| `DATABASE_URL` | Python analysis + ingestion | Neon/PostgreSQL connection; also enables DB-backed valuation |
| `FIN_ENGINE_AUTO_REFRESH` | Python analysis service | `true` (default) enables non-blocking startup and periodic public-source freshness checks when Neon is configured |
| `FIN_ENGINE_REFRESH_CHECK_HOURS` | Python analysis service | How often to check due sources while running (default 12 hours; minimum 1) |
| `DASHBOARD_VEHICLE_MAKE` | dashboard server | POC selected make |
| `DASHBOARD_VEHICLE_MODEL` | dashboard server | POC selected model |
| `DASHBOARD_VEHICLE_YEAR` | dashboard server | POC selected year |
| `DASHBOARD_VEHICLE_REGION` | dashboard server | POC selected region |

For the dashboard, start from:

```bash
cp apps/dashboard/.env.example apps/dashboard/.env.local
```

The dashboard's `ANALYSIS_BASE_URL` is server-side. Do not expose it as a `NEXT_PUBLIC_*` variable.

## Valuation data-source behavior

The Python valuation endpoint now has two explicit data paths:

```text
DATABASE_URL configured
        ↓
latest listing observation per vehicle_record
        ↓
PostgreSQL / Neon
        ↓
comparable_market_db_v1
```

If `DATABASE_URL` is not configured:

```text
VEHICLE_DATA_PATH
        ↓
committed development CSV
        ↓
comparable_market_v1
```

There is no silent DB-to-CSV fallback when a database is configured but has no comparables. The API returns no-comparables instead, allowing the dashboard to label its POC fallback honestly.

## Start the full local application stack

After the bootstrap steps above, the normal local-development command is simply:

```bash
yarn dev
```

It starts the three interactive application components together:

```text
Dashboard   http://localhost:3000
API         http://localhost:8000
Analysis    http://localhost:8001
```

The command starts **automatic best-effort public government data refresh** from the Python analysis service when `DATABASE_URL` is configured. The refresh runs in the background, so API requests do not wait for BPS, NJKB or DJP. It checks freshness at startup and every 12 hours while running. A PostgreSQL advisory lock prevents multiple analysis workers from refreshing simultaneously. A public source failure is logged and does not shut down the API.

**Permission-gated OLX, Mobil123 and Carmudi crawlers are never started automatically**; they still require explicit authorization and separate batch jobs.

`Ctrl+C` stops the full stack. If one application exits unexpectedly, the launcher stops the remaining processes instead of leaving a partially running stack behind.

The launcher automatically loads the root `.env.local` as described
above. You can still override individual settings using environment variables
in the terminal when needed:

```bash
# Git Bash / macOS / Linux only:
export DATABASE_URL='postgresql://USER:PASSWORD@HOST-pooler.../neondb?sslmode=require'
yarn dev
```

Without `DATABASE_URL`, the analysis service uses the committed development comparable CSV through the default `VEHICLE_DATA_PATH`.

## Updating public data

For a one-off refresh of only stale sources:

```bash
yarn refresh:data
```

To re-fetch all configured public government sources even if recent:

```bash
yarn refresh:data --force
```

The command writes successful results to Neon. Official NJKB is due after 90 days, BPS vehicle stock after 30 days, and DJP auction announcements after 7 days; all intervals are configurable in `apps/analysis/riil_analysis/refresh.py`. Source release years are still determined by `config/sources.py`, not by scraping an arbitrary new year's publication. Nothing fetches automatically without a configured `DATABASE_URL`.

For updates **even when your laptop and API are switched off**, GitHub Actions includes a weekly refresh schedule. Configure the repository secret `FIN_ENGINE_DATABASE_URL` (your Neon database URL) in GitHub Settings → Secrets and variables → Actions; use the Actions tab → *Refresh official public data* → *Run workflow* to verify the first run. The weekly schedule then checks what is due. This requires GitHub-hosted runners to reach Neon and the public sources. Browser fallback for BPS is installed by that workflow. The workflow does not perform migrations or restricted marketplace crawls.

## Run individual components manually

The commands below remain useful when debugging only one part of the system.

### Analysis service

From repository root:

```bash
yarn dev:analysis
```

The direct equivalent from `apps/analysis` (using the already-created virtual environment) is:

```bash
# macOS/Linux:
./.venv/bin/python -m uvicorn riil_analysis.main:app --reload --port 8001

# Windows (PowerShell or Git Bash):
./.venv/Scripts/python.exe -m uvicorn riil_analysis.main:app --reload --port 8001
```

Check:

```bash
curl http://localhost:8001/health
```

### Business dashboard

From repository root:

```bash
yarn dev:dashboard
```

Open:

```text
http://localhost:3000
```

The dashboard calls the Python analysis service server-side. Its visible data-status panel reports one of:

```text
Analysis engine · Neon observations
Analysis engine · development comparables
Fallback POC data
```

Routes:

```text
/              Executive Overview
/vehicle       Vehicle Intelligence
/market        Market Intelligence
/methodology   Data & Methodology
```

See [DASHBOARD.md](./DASHBOARD.md).

### TypeScript public API

```bash
yarn dev:api
```

Check:

```bash
curl http://localhost:8000/health
```

The dashboard does not require the public API for the POC analytical path. External/customer API contracts still belong in `apps/api`.

## Database setup

After setting `DATABASE_URL`:

```bash
yarn migrate upgrade head
```

Inspect migration state:

```bash
yarn migrate current
yarn migrate history
```

See [DATABASE.md](./DATABASE.md).

## Populate observed marketplace data

A DB-backed dashboard needs listing observations in Neon that match the selected make/model/year/region.

Example authorized crawl:

```bash
yarn ingest \
  --source mobil123_authorized_crawl \
  --authorization-ref "permission-reference" \
  --request-delay-seconds 2 \
  --limit 5 \
  --persist-db \
  --output ../../data/generated/mobil123-small.csv
```

The analysis endpoint uses only the latest listing observation per stable source record for a current comparable snapshot, so repeated crawls do not overweight the same listing.

See [INGESTION.md](./INGESTION.md).

## Tests and builds

Check the Node launcher itself on any operating system:

```bash
yarn test:tooling
```


Python:

```bash
yarn test:analysis -v
```

TypeScript API:

```bash
yarn typecheck:api
yarn build:api
```

Dashboard:

```bash
yarn typecheck:dashboard
yarn build:dashboard
```

Public API behavior should also be exercised through the Git-tracked Bruno collection under `bruno/`. Dashboard-only internal data-adapter changes do not require Bruno unless a public API contract changes.

## Docker Compose

```bash
docker compose up --build
```

Compose currently runs the public TypeScript API and Python analysis service. The dashboard is run directly through Next.js for the POC and is not yet included in Compose. For the complete local three-component stack, prefer `yarn dev`.

## Generated data

`data/generated/` is ignored by Git and intended for local inspection/debugging. Production-oriented canonical observations should persist to PostgreSQL.

## Troubleshooting

### Dashboard shows `Fallback POC data`

Check the analysis service first:

```bash
curl http://localhost:8001/health
```

Then confirm the dashboard server uses:

```text
ANALYSIS_BASE_URL=http://localhost:8001
```

If the analysis service is reachable but reports no comparables, either populate matching marketplace rows in Neon or change the dashboard POC vehicle selection to a segment that exists in the configured analysis source.

### Dashboard shows development comparables

The dashboard is connected to the Python analysis service, but that service does not have `DATABASE_URL` configured. This is valid for local development but must not be described as observed marketplace data.

### Public API returns `502 analysis_unavailable`

Confirm the Python service is running and that the API's `ANALYSIS_BASE_URL` is correct.
