#!/usr/bin/env bash
# Quick end-to-end check against a running stack. Reads API_KEY from .env.
set -euo pipefail
cd "$(dirname "$0")/.."
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="$(grep -E '^API_KEY=' .env | cut -d= -f2-)"

echo "health:  $(curl -fsS "$BASE_URL/health")"
echo "ready:   $(curl -fsS "$BASE_URL/ready")"
echo "version: $(curl -fsS "$BASE_URL/version")"
echo "create:  $(curl -fsS -X POST "$BASE_URL/operations" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"name":"smoke test operation"}')"
echo "list:    $(curl -fsS "$BASE_URL/operations")"
echo "metrics: $(curl -fsS "$BASE_URL/metrics" | grep -c apex_) apex_ metric lines"
echo "SMOKE TEST PASSED"
