# Deployment

Fin Engine is designed to run ingestion as short-lived batch jobs and the public API as a separate long-running service.

## Target architecture

```text
Cloud Scheduler
      ↓
Cloud Run Job
      ↓
Fin Engine ingestion CLI
      ↓
Neon PostgreSQL

TypeScript public API / Python analysis service
      ↓
separate service deployment
```

## Current repository status

Implemented today:

```text
✓ ingestion CLI
✓ authorized marketplace crawlers
✓ official-source adapters
✓ rate limiting/backoff
✓ Neon/PostgreSQL persistence
✓ Alembic migrations
✓ Python API Dockerfile
```

Not yet committed as deployment infrastructure:

```text
○ dedicated ingestion-job Dockerfile/entrypoint
○ Artifact Registry configuration
○ Cloud Run Job definitions
○ Secret Manager bindings
○ Cloud Scheduler definitions
○ CI/CD deployment workflow
```

Do not read this document as evidence that a Cloud Run Job is already deployed.

## Why Cloud Run Jobs

The ingestion workload is naturally batch-oriented:

```text
start
→ fetch source
→ normalize
→ persist
→ exit
```

A crawler does not need to stay online between runs, so a job model is simpler and more cost-efficient than a permanently running server.

## Database

Use Neon PostgreSQL as the initial durable database.

Prefer the pooled connection string for Cloud Run Jobs.

Store it in Google Secret Manager as a secret mapped to:

```text
DATABASE_URL
```

Do not put database credentials in:

- Dockerfiles;
- source code;
- GitHub repository variables visible in logs;
- Cloud Scheduler URLs;
- command arguments that may be logged.

## Marketplace authorization references

Authorized live crawlers require:

```text
--authorization-ref
```

For cloud deployment, prefer injecting a reference identifier from a secret or environment variable rather than hard-coding it in the image.

The reference should identify the applicable permission/contract/ticket, not contain the full legal document or credentials.

## Recommended job topology

Start with one Cloud Run Job per source:

```text
fin-engine-olx
fin-engine-mobil123
fin-engine-carmudi
fin-engine-djp-auction
fin-engine-njkb
```

Benefits:

- independent schedules;
- independent retries;
- easier per-source logs;
- one broken source does not block all sources;
- source-specific limits can differ.

Do not create parallel tasks for the same marketplace until the approved crawl rate and source behavior justify it. Current crawler design assumes sequential requests.

## Recommended marketplace defaults

Initial cloud smoke test:

```text
concurrency / tasks      1
request delay            2–3 seconds
record/detail limit      5
job retries              0 or 1
schedule                  manual only
```

After validation:

```text
concurrency / tasks      1
request delay            according to permission; never below code floor
record/detail limit      increase gradually, max currently 50/run
schedule                  daily or as required by product need
```

If the marketplace permission is stricter, the permission wins.

## Container requirement

The existing `apps/analysis/Dockerfile` starts FastAPI and is intended for the analysis service.

Before deploying ingestion to Cloud Run Jobs, add a dedicated job image or override command/entrypoint in a deliberate, tested way. A future job image should include:

```text
pyproject.toml
riil_analysis/
migrations/
alembic.ini
```

and install the `fin-engine-data` console script.

Conceptual job command:

```bash
fin-engine-data ingest \
  --source mobil123_authorized_crawl \
  --authorization-ref "$AUTHORIZATION_REF" \
  --request-delay-seconds 2 \
  --limit 5 \
  --persist-db
```

## Migration strategy

Do not run schema migrations concurrently from every crawler job.

Preferred approach:

```text
release/deploy step
   ↓
alembic upgrade head
   ↓
then execute crawler jobs
```

For the MVP, migration can be a manual step from a trusted developer environment.

Later, use a dedicated migration job or CI/CD deployment stage.

## Suggested Google Cloud resources

Planned resources:

```text
Artifact Registry
  fin-engine images

Secret Manager
  fin-engine-database-url
  source authorization references if needed

Cloud Run Jobs
  one per source

Cloud Scheduler
  triggers only after manual jobs are stable
```

Deploy jobs in a region close to the Neon database region when practical.

## Secret Manager permissions

Use a dedicated runtime service account for Cloud Run Jobs.

Grant only the permissions the job needs, typically:

- execute the Cloud Run Job;
- read the specific secret versions required by that job;
- write logs.

Do not grant broad project Owner/Editor privileges to the crawler runtime account.

## Logging

Every job should make the ingestion JSON result visible in Cloud Logging.

Useful fields already emitted by the CLI include:

```text
quality
created_records
updated_records
inserted_observations
run_id
```

Database `ingestion_runs` is the durable operational record. Cloud Logging is the runtime/debug record.

## Job failure semantics

A job should fail when the source cannot produce usable records or persistence fails.

Do not mark a job successful merely because HTTP requests completed.

Monitor for:

```text
zero parsed records
sharp drop in valid records
normalization failures
unexpected semantic failures
HTTP 429/503 frequency
database connection failure
migration mismatch
```

## Scheduler strategy

Do not schedule crawlers before manual runs are stable.

A reasonable early schedule is one run per day per marketplace.

NJKB is a reference dataset and does not need the same crawl frequency as marketplace listings.

Example conceptual cadence:

```text
OLX             daily
Mobil123        daily
Carmudi         daily
DJP auctions    daily/periodic
NJKB            on regulation/source update or low-frequency check
```

Schedule choices should be driven by data freshness requirements and permissions, not by maximizing request volume.

## Rollout checklist

### Before first cloud deployment

```text
[ ] local unit tests pass
[ ] migration applied to Neon
[ ] five-record live crawl works locally
[ ] data looks semantically correct
[ ] authorization reference recorded
[ ] Neon pooled URL stored as secret
[ ] job image contains ingestion CLI + migrations
```

### First Cloud Run Job

```text
[ ] deploy one source only
[ ] limit = 5
[ ] one task / no parallelism
[ ] manual execution
[ ] inspect Cloud Logging
[ ] inspect ingestion_runs
[ ] inspect vehicle_records
[ ] inspect vehicle_observations
```

### Before scheduling

```text
[ ] repeat manual job successfully
[ ] confirm same source record appends observations
[ ] confirm no unexpected duplicates
[ ] confirm crawl rate matches permission
[ ] set conservative retry behavior
[ ] create scheduler trigger
```

## Rollback

Application rollback and database rollback are separate concerns.

If a crawler parser is faulty:

1. stop/suspend its scheduled trigger;
2. revert/deploy the last known-good image;
3. inspect affected `ingestion_runs`;
4. decide whether bad observations should be marked/excluded or deleted under a controlled data repair;
5. add a regression test before re-enabling the job.

Avoid deleting historical data automatically as part of application rollback.

## Production evolution

When the platform grows, likely additions include:

```text
raw payload storage in object storage
alerting on source-quality degradation
source-specific checkpoints
feature-engine batch jobs
API deployment and authentication
separate staging/production databases
CI/CD with migration gates
```

Kubernetes is intentionally not required for this architecture.
