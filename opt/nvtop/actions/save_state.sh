#!/bin/bash
# save_state.sh - Capture nvtop screen as image
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/save_state.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting nvtop screen capture..."

# Capture current display or save to specific file
if [ -n "${SAVE_PATH:-}" ]; then
    nvtop -s "$SAVE_PATH" 2>/dev/null || log "Save failed, using default location"
else
    nvtop -s /tmp/nvtop-snapshot.png 2>/dev/null || true
fi

log "Screen capture completed at $(date)"
exit 0
