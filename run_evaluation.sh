#!/usr/bin/env bash
set -euo pipefail
EVAL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$EVAL_ROOT/fft64_benchmark/runtime.sh"
fft_runtime_init "$EVAL_ROOT/fft64_benchmark"
exec "$FFT_PYTHON" "$EVAL_ROOT/operator/evaluate_synopsys.py" --backend auto "$@"
