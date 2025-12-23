#!/bin/bash
# Entrypoint script for Cloud Run Jobs
# Allows flexible execution with CLI arguments

set -e

# Default values
SCRIPT_NAME="${SCRIPT_NAME:-main.py}"
START_DATE="${START_DATE:-}"
END_DATE="${END_DATE:-}"
VENDOR="${VENDOR:-}"

# Build command
CMD="python ${SCRIPT_NAME}"

# Add optional arguments
if [ -n "$START_DATE" ]; then
    CMD="${CMD} --start-date ${START_DATE}"
fi

if [ -n "$END_DATE" ]; then
    CMD="${CMD} --end-date ${END_DATE}"
fi

if [ -n "$VENDOR" ]; then
    CMD="${CMD} --vendor ${VENDOR}"
fi

# Execute the command
echo "Executing: ${CMD}"
exec ${CMD}

