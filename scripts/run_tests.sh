#!/usr/bin/env bash
set -e

# Navigate to script parent directory
cd "$(dirname "$0")/.."

# Activate virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

pytest -v tests/ "$@"
