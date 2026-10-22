#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID to your Google Cloud project ID}"
: "${SOURCE_ID:?Set SOURCE_ID, for example olx_authorized_crawl}"

GCP_REGION="${GCP_REGION:-asia-southeast1}"
AR_REPO="${AR_REPO:-fin-engine}"
IMAGE_TAG="${IMAGE_TAG:-marketplace-poc}"
LIMIT="${LIMIT:-5}"
REQUEST_DELAY_SECONDS="${REQUEST_DELAY_SECONDS:-2}"
DATABASE_SECRET="${DATABASE_SECRET:-fin-engine-database-url}"
RUNTIME_SERVICE_ACCOUNT_NAME="${RUNTIME_SERVICE_ACCOUNT_NAME:-fin-engine-ingestion}"
RUNTIME_SERVICE_ACCOUNT="${RUNTIME_SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

case "$SOURCE_ID" in
  olx_authorized_crawl)
    JOB_NAME="${JOB_NAME:-fin-engine-olx}"
    AUTHORIZATION_SECRET="${AUTHORIZATION_SECRET:-fin-engine-olx-authorization}"
    ;;
  mobil123_authorized_crawl)
    JOB_NAME="${JOB_NAME:-fin-engine-mobil123}"
    AUTHORIZATION_SECRET="${AUTHORIZATION_SECRET:-fin-engine-mobil123-authorization}"
    ;;
  carmudi_authorized_crawl)
    JOB_NAME="${JOB_NAME:-fin-engine-carmudi}"
    AUTHORIZATION_SECRET="${AUTHORIZATION_SECRET:-fin-engine-carmudi-authorization}"
    ;;
  *)
    echo "Unsupported marketplace SOURCE_ID: $SOURCE_ID" >&2
    echo "Supported values: olx_authorized_crawl, mobil123_authorized_crawl, carmudi_authorized_crawl" >&2
    exit 2
    ;;
esac

IMAGE_URI="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${AR_REPO}/ingestion-job:${IMAGE_TAG}"

printf '\nFin Engine Cloud Run Job deployment\n'
printf '  Project    %s\n' "$GCP_PROJECT_ID"
printf '  Region     %s\n' "$GCP_REGION"
printf '  Source     %s\n' "$SOURCE_ID"
printf '  Job        %s\n' "$JOB_NAME"
printf '  Image      %s\n' "$IMAGE_URI"
printf '  Limit      %s\n' "$LIMIT"
printf '  Delay      %ss\n\n' "$REQUEST_DELAY_SECONDS"

gcloud config set project "$GCP_PROJECT_ID" >/dev/null

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  --project "$GCP_PROJECT_ID" >/dev/null

if ! gcloud artifacts repositories describe "$AR_REPO" \
  --location "$GCP_REGION" \
  --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$AR_REPO" \
    --repository-format docker \
    --location "$GCP_REGION" \
    --description "Fin Engine container images" \
    --project "$GCP_PROJECT_ID"
fi

if ! gcloud iam service-accounts describe "$RUNTIME_SERVICE_ACCOUNT" \
  --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$RUNTIME_SERVICE_ACCOUNT_NAME" \
    --display-name "Fin Engine ingestion runtime" \
    --project "$GCP_PROJECT_ID"
fi

for secret in "$DATABASE_SECRET" "$AUTHORIZATION_SECRET"; do
  if ! gcloud secrets describe "$secret" \
    --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
    echo "Required Secret Manager secret does not exist: $secret" >&2
    echo "Create it before deploying this job." >&2
    exit 3
  fi

  gcloud secrets add-iam-policy-binding "$secret" \
    --member "serviceAccount:${RUNTIME_SERVICE_ACCOUNT}" \
    --role roles/secretmanager.secretAccessor \
    --project "$GCP_PROJECT_ID" >/dev/null
 done

gcloud builds submit "$ROOT_DIR/apps/analysis" \
  --project "$GCP_PROJECT_ID" \
  --config "$ROOT_DIR/apps/analysis/cloudbuild.job.yaml" \
  --substitutions "_IMAGE_URI=${IMAGE_URI}"

COMMON_ARGS=(
  --image "$IMAGE_URI"
  --region "$GCP_REGION"
  --project "$GCP_PROJECT_ID"
  --tasks 1
  --max-retries 0
  --task-timeout 15m
  --service-account "$RUNTIME_SERVICE_ACCOUNT"
  --set-env-vars "SOURCE_ID=${SOURCE_ID},LIMIT=${LIMIT},REQUEST_DELAY_SECONDS=${REQUEST_DELAY_SECONDS}"
  --set-secrets "DATABASE_URL=${DATABASE_SECRET}:latest,AUTHORIZATION_REF=${AUTHORIZATION_SECRET}:latest"
)

if gcloud run jobs describe "$JOB_NAME" \
  --region "$GCP_REGION" \
  --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
  gcloud run jobs update "$JOB_NAME" "${COMMON_ARGS[@]}"
else
  gcloud run jobs create "$JOB_NAME" "${COMMON_ARGS[@]}"
fi

printf '\nDeployment complete. Execute manually with:\n\n'
printf 'gcloud run jobs execute %s --region %s --project %s --wait\n\n' \
  "$JOB_NAME" "$GCP_REGION" "$GCP_PROJECT_ID"
