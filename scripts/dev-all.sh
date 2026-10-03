#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS=""

cleanup() {
  status=$?
  trap - EXIT INT TERM

  if [ -n "$PIDS" ]; then
    for pid in $PIDS; do
      kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
  fi

  exit "$status"
}

trap cleanup EXIT INT TERM

printf '\nFin Engine local stack\n'
printf '  Dashboard  http://localhost:3000\n'
printf '  API        http://localhost:8000\n'
printf '  Analysis   http://localhost:8001\n'
printf '  Crawlers   not started\n\n'

(
  cd "$ROOT_DIR/apps/analysis"
  export VEHICLE_DATA_PATH="${VEHICLE_DATA_PATH:-../../data/sample/vehicles.csv}"
  exec uv run uvicorn riil_analysis.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8001
) &
PIDS="$PIDS $!"

(
  cd "$ROOT_DIR"
  export ANALYSIS_BASE_URL="${ANALYSIS_BASE_URL:-http://localhost:8001}"
  exec yarn dev:api
) &
PIDS="$PIDS $!"

(
  cd "$ROOT_DIR"
  export ANALYSIS_BASE_URL="${ANALYSIS_BASE_URL:-http://localhost:8001}"
  exec yarn dev:dashboard
) &
PIDS="$PIDS $!"

# Portable process supervision for macOS' system Bash as well as newer Bash.
# If one application exits unexpectedly, stop the rest rather than leaving a
# partially running development stack behind.
while true; do
  for pid in $PIDS; do
    if ! kill -0 "$pid" 2>/dev/null; then
      printf '\nA Fin Engine component exited; stopping the remaining local services.\n' >&2
      exit 1
    fi
  done
  sleep 1
done
