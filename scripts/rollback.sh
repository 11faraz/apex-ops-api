#!/usr/bin/env bash
# Usage: scripts/rollback.sh [version]   (defaults to the version recorded in .release/previous)
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

# Never carry demo fault flags into a rollback.
unset FAULT_INJECTION

TARGET="${1:-$(read_state previous)}"
if [ -z "$TARGET" ]; then
  echo "No version given and .release/previous is empty." >&2
  exit 1
fi
if ! docker image inspect "apex-ops-api:$TARGET" >/dev/null 2>&1; then
  echo "Image apex-ops-api:$TARGET does not exist locally, cannot roll back." >&2
  exit 1
fi

CURRENT="$(read_state current)"
echo "==> Rolling back ${CURRENT:-unknown} -> $TARGET"
export APP_VERSION="$TARGET"
docker compose up -d --no-build

wait_ready "$TARGET"
[ -n "$CURRENT" ] && [ "$CURRENT" != "$TARGET" ] && echo "$CURRENT" > "$STATE_DIR/previous"
echo "$TARGET" > "$STATE_DIR/current"
echo "==> Rollback to $TARGET complete (data volume untouched)"
