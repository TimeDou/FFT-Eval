#!/usr/bin/env bash
# Install the numerical dependency and inspect the selected EDA environment.
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -r /etc/profile.d/eda-env.sh ]]; then set +u; source /etc/profile.d/eda-env.sh; set -u; fi
TASK_PY="${FFT_PYTHON:-python3}"
if [[ -z "${FFT_PYTHON:-}" && -x /opt/dsbench/bin/python3 ]]; then TASK_PY=/opt/dsbench/bin/python3; fi
if ! "$TASK_PY" -c 'import numpy' >/dev/null 2>&1; then
  if "$TASK_PY" -c 'import sys; assert sys.version_info[:2] == (3,12)' >/dev/null 2>&1; then
    "$TASK_PY" -m pip install --no-index --find-links "$TASK_DIR/vendor/wheels" -r "$TASK_DIR/requirements.txt"
  else
    "$TASK_PY" -m pip install -r "$TASK_DIR/requirements.txt"
  fi
fi
if [[ "${1:-commercial}" == commercial && ( ! -s "$TASK_DIR/tech/db/comb_rvt_tt.db" || ! -s "$TASK_DIR/tech/db/seq_rvt_tt.db" ) ]]; then
  if command -v "${FFT_LC_BIN:-lc_shell}" >/dev/null 2>&1; then
    "${FFT_LC_BIN:-lc_shell}" -f "$TASK_DIR/flow/compile_libraries.tcl" > "$TASK_DIR/tech/library_compile.log" 2>&1
  else
    printf '%s\n' 'Library Compiler is unavailable. Provide the matching comb/seq DBs under tech/db/ before commercial evaluation.'
  fi
fi
"$TASK_PY" "$TASK_DIR/tools/environment.py" --backend "${1:-commercial}"
