#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/sample-app"

cd "$APP_DIR"

# Remove dream state files
rm -f .dream-state-*.local.yaml

# Remove generated specs but preserve the Mode A fixture
find docs/specs -name "*-spec.md" ! -name "existing-spec.md" -delete 2>/dev/null || true
find docs/specs -name "epic-*-phases.md" -delete 2>/dev/null || true

echo "Reset complete. State files and generated specs removed."
echo "Preserved: docs/specs/existing-spec.md"
