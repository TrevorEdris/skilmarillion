#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/sample-app"

cd "$APP_DIR"

# Remove all skilmarillion output (state files, generated specs, session artifacts)
rm -rf .skilmarillion/

echo "Reset complete. .skilmarillion/ directory removed."
