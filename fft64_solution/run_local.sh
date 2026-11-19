#!/usr/bin/env bash
set -euo pipefail
SOLUTION_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
"${FFT_PYTHON:-python3}" "$SOLUTION_DIR/tools/solve.py" --holdout "$@"
