#!/usr/bin/env bash
# Shared helpers for deploy.sh and rollback.sh
STATE_DIR=".release"
BASE_URL="${BASE_URL:-http://localhost:8000}"
WAIT_SECONDS="${WAIT_SECONDS:-45}"

mkdir -p "$STATE_DIR"

read_state() { cat "$STATE_DIR/$1" 2>/dev/null || true; }

# Wait until /ready answers 200 and /version reports the expected version.
wait_ready() {
  local expected="$1" waited=0
  while [ "$waited" -lt "$WAIT_SECONDS" ]; do
    if curl -fsS "$BASE_URL/ready" >/dev/null 2>&1; then
      local running
      running="$(curl -fsS "$BASE_URL/version" | sed -E 's/.*"version": *"([^"]+)".*/\1/')"
      if [ "$running" = "$expected" ]; then
        echo "OK: version $running is ready"
        return 0
      fi
    fi
    sleep 2
    waited=$((waited + 2))
  done
  echo "FAILED: version $expected did not become ready within ${WAIT_SECONDS}s" >&2
  return 1
}
