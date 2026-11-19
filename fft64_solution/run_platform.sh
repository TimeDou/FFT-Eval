#!/usr/bin/env bash
# The reference uses exactly the same fixed commercial scorer as agent designs.
set -euo pipefail
SOLUTION_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SOLUTION_DIR/../run_synopsys.sh" "$SOLUTION_DIR" --origin reference --agent author "$@"
