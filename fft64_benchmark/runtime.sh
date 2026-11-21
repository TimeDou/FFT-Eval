#!/usr/bin/env bash
# Shared entrypoint: reuse DSBench's configured tools and Python first.
fft_runtime_init() {
  local task_dir="$1" candidate
  local profile="${FFT_EDA_PROFILE:-/etc/profile.d/eda-env.sh}"
  if [[ -r "$profile" ]]; then set +u; source "$profile"; set -u; export FFT_EDA_PROFILE_LOADED=1; fi
  if [[ -z "${FFT_PYTHON:-}" ]]; then
    for candidate in /opt/dsbench/bin/python3 "$(command -v python3 || true)"; do
      if [[ -n "$candidate" && -x "$candidate" ]] && "$candidate" -c 'import sys; assert sys.version_info >= (3,10)' >/dev/null 2>&1; then
        export FFT_PYTHON="$candidate"
        break
      fi
    done
  fi
  if [[ -z "${FFT_PYTHON:-}" ]] || ! "$FFT_PYTHON" -c 'import sys; assert sys.version_info >= (3,10)' >/dev/null 2>&1; then
    printf '%s\n' 'Python 3.10+ is required. DSBench provides /opt/dsbench/bin/python3; set FFT_PYTHON if needed.' >&2
    return 2
  fi
  if [[ -z "${FFT_TOOLS_PREFIX:-}" ]]; then
    if [[ -d /workspace ]]; then export FFT_TOOLS_PREFIX=/workspace/.fft64-tools
    else export FFT_TOOLS_PREFIX="$(cd -- "$task_dir/.." && pwd)/.fft64-tools"; fi
  fi
  if [[ -d "$FFT_TOOLS_PREFIX/bin" ]]; then export PATH="${PATH:-}:$FFT_TOOLS_PREFIX/bin"; fi
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
}
