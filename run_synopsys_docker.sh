#!/usr/bin/env bash
# Host entrypoint; password authentication stays with the SSH client.
set -euo pipefail
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${FFT_HOST_PYTHON:-python3}" "$REPO_DIR/operator/docker_runner.py" "$@"
