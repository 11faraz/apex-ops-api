#!/usr/bin/env bash
# Usage: scripts/deploy.sh <version>      e.g. scripts/deploy.sh 1.1.0
# Builds a versioned image, starts it, and rolls back automatically if it never becomes ready.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

VERSION="${1:?usage: scripts/deploy.sh <version>}"
PREVIOUS="$(read_state current)"

echo "==> Building apex-ops-api:$VERSION"
docker build --build-arg APP_VERSION="$VERSION" -t "apex-ops-api:$VERSION" .

echo "==> Starting version $VERSION (previous: ${PREVIOUS:-none})"
export APP_VERSION="$VERSION"
docker compose up -d --no-build

if wait_ready "$VERSION"; then
  if [ -n "$PREVIOUS" ] && [ "$PREVIOUS" != "$VERSION" ]; then
    echo "$PREVIOUS" > "$STATE_DIR/previous"
  fi
  echo "$VERSION" > "$STATE_DIR/current"
  echo "==> Deployed $VERSION"
else
  if [ -n "$PREVIOUS" ] && [ "$PREVIOUS" != "$VERSION" ]; then
    echo "==> Release failed health checks, rolling back to $PREVIOUS" >&2
    scripts/rollback.sh "$PREVIOUS"
  else
    echo "==> Release failed and there is no previous version to roll back to" >&2
  fi
  exit 1
fi
