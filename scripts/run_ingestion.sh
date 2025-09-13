#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
export DATA_DIR=${DATA_DIR:-data}
# export PROM_PORT=9108
# export PANDASCORE_TOKEN=...
python -m main
