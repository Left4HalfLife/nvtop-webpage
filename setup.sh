#!/bin/bash
# One-time Docker Compose setup.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

command -v docker >/dev/null || {
    echo "Docker is required." >&2
    exit 1
}
command -v openssl >/dev/null || {
    echo "OpenSSL is required to generate credentials." >&2
    exit 1
}

mkdir -p instance/logs
chmod 700 instance/logs

if [[ ! -f .env ]]; then
    umask 077
    {
        echo "NVTOP_AUTH_USER=nvtop-admin"
        echo "NVTOP_AUTH_PASSWORD=$(openssl rand -base64 32)"
        echo "NVTOP_SECRET_KEY=$(openssl rand -hex 32)"
    } > .env
    echo "Created .env with random credentials."
else
    echo "Using existing .env."
fi

chmod 600 .env
docker compose config >/dev/null
docker compose build

echo "Setup complete. Run: docker compose up -d"
echo "Then open: http://127.0.0.1:5001"