#!/bin/bash
# setup.sh - One-time setup for nvtop-webpage container
# Run this once before starting the Docker container
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="nvtop-webapp"

echo "=== NVTop Webpage Container Setup ==="

# Create necessary directories inside container
docker run --rm \
  --name nvtop-temp \
  --entrypoint "" \
  -v "${SCRIPT_DIR}:/app:ro" \
  nvtop-webapp \
  mkdir -p /app/instance/logs \
  mkdir -p /opt/nvtop/actions/logs

# Copy config if exists, otherwise create default
CONFIG_FILE="${SCRIPT_DIR}/instance/config.json"
if [ ! -f "$CONFIG_FILE" ] && [ -f "${SCRIPT_DIR}/instance/config.json.example" ]; then
    echo "Config not found. Using example template."
    docker run --rm \
      --name nvtop-temp2 \
      --entrypoint "" \
      -v "${SCRIPT_DIR}:/app:ro" \
      nvtop-webapp \
      cp /app/instance/config.json.example /app/instance/config.json
    
    echo "⚠️  WARNING: Remember to set AUTH_PASSWORD before starting!"
else
    if [ -f "$CONFIG_FILE" ]; then
        echo "Using existing config.json"
    fi
fi

# Remove temp containers
docker rm -f nvtop-temp >/dev/null 2>&1 || true
docker rm -f nvtop-temp2 >/dev/null 2>&1 || true

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the container:"
echo "  docker-compose up -d"
echo ""
echo "Or directly:"
echo "  docker run -d \\"
echo "    --name nvtop-webapp \\"
echo "    -p 5000:5000 \\"
echo "    -e AUTH_USER=\"nvtop-admin\" \\"
echo "    -e AUTH_PASSWORD=\"your-secret-password\" \\"
echo "    nvtop-webapp"
