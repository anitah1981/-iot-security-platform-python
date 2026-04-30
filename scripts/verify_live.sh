#!/usr/bin/env bash
# Post-deploy smoke tests. From repo root:
#   LIVE_URL=https://your-domain.com ./scripts/verify_live.sh
# Optional: TEST_EMAIL TEST_PASSWORD
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
URL="${LIVE_URL:-${1:-}}"
if [[ -z "$URL" ]]; then
  echo "Usage: LIVE_URL=https://your-domain.com $0" >&2
  echo "   or: $0 https://your-domain.com" >&2
  exit 2
fi
exec python3 scripts/verify_live.py "$URL"
