#!/usr/bin/env bash
# Re-evaluate RTL from any generation platform in the fixed Synopsys flow.
set -euo pipefail
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$REPO_DIR/fft64_benchmark/runtime.sh"
fft_runtime_init "$REPO_DIR/fft64_benchmark"
exec "$FFT_PYTHON" "$REPO_DIR/operator/evaluate_synopsys.py" "$@"
