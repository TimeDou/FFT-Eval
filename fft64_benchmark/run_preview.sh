#!/usr/bin/env bash
# Usage: bash run_preview.sh SUBMISSION OUTPUT [--backend local] [--quick]
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -r /etc/profile.d/eda-env.sh ]]; then set +u; source /etc/profile.d/eda-env.sh; set -u; fi
TASK_PY="${FFT_PYTHON:-python3}"
if [[ -z "${FFT_PYTHON:-}" && -x /opt/dsbench/bin/python3 ]]; then TASK_PY=/opt/dsbench/bin/python3; fi
TASK_SUBMISSION="${1:-/workspace/submission}"
TASK_OUTPUT="${2:-$TASK_SUBMISSION/runs/preview_$(date +%Y%m%d_%H%M%S)}"
if [[ $# -ge 2 ]]; then shift 2; elif [[ $# -eq 1 ]]; then shift; fi
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
TASK_OPTIONS=()
if [[ -n "${FFT_CALIBRATION:-}" ]]; then TASK_OPTIONS+=(--calibration "$FFT_CALIBRATION"); fi
"$TASK_PY" "$TASK_DIR/tools/evaluate.py" --submission "$TASK_SUBMISSION" --out "$TASK_OUTPUT" "${TASK_OPTIONS[@]}" "$@"
