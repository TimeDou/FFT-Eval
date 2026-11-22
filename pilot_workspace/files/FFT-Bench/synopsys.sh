#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${FFT_HOST_PYTHON:-python3}" "$REPO_DIR/fft64_benchmark/tools/synopsys_remote.py" "$@"
