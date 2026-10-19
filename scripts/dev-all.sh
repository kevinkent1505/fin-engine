#!/usr/bin/env bash
# Legacy convenience wrapper; yarn dev is platform-independent.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec node "$ROOT_DIR/scripts/fin-engine.mjs" dev
