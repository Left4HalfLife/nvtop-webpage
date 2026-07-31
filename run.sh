#!/bin/bash
# run.sh - Start nvtop web app
# Usage: ./run.sh [options]
#   --auth-user USER    Set authentication username (default: nvtop-admin)
#   --auth-password PASS Set authentication password
#   --port PORT         Set port (default: 5000)

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${APP_DIR}/instance/config.json"

# Default values
AUTH_USER="nvtop-admin"
AUTH_PASSWORD=""
PORT=5000

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auth-user)
            AUTH_USER="$2"
            shift 2
            ;;
        --auth-password)
            AUTH_PASSWORD="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create instance directory if it doesn't exist
mkdir -p "${APP_DIR}/instance"

# Set permissions (restrictive for security)
chmod 700 "${APP_DIR}/instance"

# Export environment variables
export AUTH_USER="${AUTH_USER}"
export AUTH_PASSWORD="${AUTH_PASSWORD}"
export PORT="${PORT}"
export CONFIG_PATH="${CONFIG_FILE}"
export FLASK_ENV="production"

# Generate a secure random token for auth if not provided
if [ -z "${AUTH_TOKEN:-}" ]; then
    export AUTH_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
fi

echo "Starting nvtop web app..."
echo "Auth user: ${AUTH_USER}"
echo "Auth token set: ${AUTH_TOKEN:0:16}..."

# Run with uvicorn (or gunicorn if installed)
if command -v python3 &> /dev/null; then
    cd "${APP_DIR}"
    exec python3 app.py
else
    echo "Python3 not found, exiting"
    exit 1
fi
