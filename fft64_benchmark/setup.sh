#!/usr/bin/env bash
# Reuse Synopsys, then installed open-source tools, then build missing tools.
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$TASK_DIR/runtime.sh"
fft_runtime_init "$TASK_DIR"
TASK_BACKEND="${FFT_BACKEND:-auto}"
if [[ "${1:-}" == auto || "${1:-}" == commercial || "${1:-}" == local ]]; then TASK_BACKEND="$1"; shift; fi
"$FFT_PYTHON" "$TASK_DIR/tools/environment.py" --backend "$TASK_BACKEND" "$@"
