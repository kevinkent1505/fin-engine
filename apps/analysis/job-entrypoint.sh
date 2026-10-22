#!/bin/sh
set -eu

: "${SOURCE_ID:?SOURCE_ID is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"

set -- ingest \
  --source "$SOURCE_ID" \
  --persist-db

if [ -n "${LIMIT:-}" ]; then
  set -- "$@" --limit "$LIMIT"
fi

if [ -n "${REQUEST_DELAY_SECONDS:-}" ]; then
  set -- "$@" --request-delay-seconds "$REQUEST_DELAY_SECONDS"
fi

if [ -n "${AUTHORIZATION_REF:-}" ]; then
  set -- "$@" --authorization-ref "$AUTHORIZATION_REF"
fi

if [ -n "${START_URL:-}" ]; then
  set -- "$@" --start-url "$START_URL"
fi

if [ -n "${INPUT_FILE:-}" ]; then
  set -- "$@" --input-file "$INPUT_FILE"
fi

if [ -n "${OUTPUT_PATH:-}" ]; then
  set -- "$@" --output "$OUTPUT_PATH"
fi

exec fin-engine-data "$@"
