#!/bin/bash
# unload_lms.sh - Unload LMS from GPU memory
# Runs as a dedicated low-privilege user with restricted permissions
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/unload_lms.log"

# Log action
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting unload_lms..." | tee -a "$LOG_FILE"

# Execute the actual unload operation
# This should be replaced with your actual LMS unload mechanism
# Example: using nvidia-smi to unload a process
nvidia-smi -c 0,1 GPU 0 unload || true

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Unload completed" | tee -a "$LOG_FILE"
exit 0
