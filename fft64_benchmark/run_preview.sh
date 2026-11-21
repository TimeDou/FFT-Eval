#!/usr/bin/env bash
# Usage: bash run_preview.sh SUBMISSION OUTPUT [--backend auto|commercial|local] [--profile area|architecture] [--quick] [--no-build]
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$TASK_DIR/runtime.sh"
fft_runtime_init "$TASK_DIR"
if [[ "${1:-}" == --help ]]; then printf '%s\n' 'Usage: bash run_preview.sh SUBMISSION OUTPUT [--backend auto|commercial|local] [--profile area|architecture] [--quick] [--no-build]'; exit 0; fi
TASK_SUBMISSION="${1:-/workspace/submission}"
TASK_OUTPUT="${2:-$TASK_SUBMISSION/runs/preview_$(date +%Y%m%d_%H%M%S)}"
if [[ $# -ge 2 ]]; then shift 2; elif [[ $# -eq 1 ]]; then shift; fi
mkdir -p "$TASK_OUTPUT"
TASK_OPTIONS=()
if [[ -n "${FFT_CALIBRATION:-}" ]]; then TASK_OPTIONS+=(--calibration "$FFT_CALIBRATION"); fi
TASK_PREP=(--backend "${FFT_BACKEND:-auto}")
if [[ -n "${FFT_CALIBRATION:-}" ]]; then TASK_PREP+=(--calibration "$FFT_CALIBRATION"); fi
TASK_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend|--calibration)
      TASK_PREP+=("$1" "$2"); TASK_ARGS+=("$1" "$2"); shift 2 ;;
    --backend=*|--calibration=*) TASK_PREP+=("$1"); TASK_ARGS+=("$1"); shift ;;
    --quick) TASK_PREP+=(--quick); TASK_ARGS+=(--quick); shift ;;
    --no-build) TASK_PREP+=(--no-build); shift ;;
    *) TASK_ARGS+=("$1"); shift ;;
  esac
done
if [[ "${FFT_NO_BUILD:-0}" == 1 ]]; then TASK_PREP+=(--no-build); fi
if ! "$FFT_PYTHON" "$TASK_DIR/tools/environment.py" "${TASK_PREP[@]}" --report "$TASK_OUTPUT/environment_selection.json" --env-file "$TASK_OUTPUT/runtime_environment.sh" > "$TASK_OUTPUT/environment_setup.log" 2>&1; then
  cat "$TASK_OUTPUT/environment_setup.log"
  exit 2
fi
source "$TASK_OUTPUT/runtime_environment.sh"
"$FFT_PYTHON" "$TASK_DIR/tools/evaluate.py" --submission "$TASK_SUBMISSION" --out "$TASK_OUTPUT" --backend "$FFT_SELECTED_BACKEND" "${TASK_OPTIONS[@]}" "${TASK_ARGS[@]}"
