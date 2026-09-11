#!/bin/bash
# run.sh - Start nvtop web app
# Set AUTH_PASSWORD and SECRET_KEY in the environment before running.

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${APP_DIR}/instance/config.json"

: "${AUTH_PASSWORD:?Set AUTH_PASSWORD before running}"
: "${SECRET_KEY:?Set SECRET_KEY before running}"
export AUTH_USER="${AUTH_USER:-nvtop-admin}"
export PORT="${PORT:-5000}"

# Create instance directory if it doesn't exist
mkdir -p "${APP_DIR}/instance"

# Set permissions (restrictive for security)
chmod 700 "${APP_DIR}/instance"

# Export environment variables
export CONFIG_PATH="${CONFIG_FILE}"

echo "Starting nvtop web app..."
echo "Auth user: ${AUTH_USER}"
cd "${APP_DIR}"
exec python3 app.py
