#!/usr/bin/env bash
# Optional profile for the local Synopsys container. Existing explicit
# environment choices take precedence. No license files or credentials are copied.
export FFT_CONTAINER_SHARE="${FFT_CONTAINER_SHARE:-/mnt/mydata}"
export VCS_HOME="${VCS_HOME:-/usr/synopsys/vcs-L-2016.06}"
export DC_HOME="${DC_HOME:-/usr/synopsys/dc-L-2016.03-SP1}"
export PT_HOME="${PT_HOME:-/usr/synopsys/pt-M-2016.12-SP1}"
export LC_HOME="${LC_HOME:-/usr/synopsys/lc-M-2016.12}"
export PATH="$VCS_HOME/bin:$DC_HOME/bin:$PT_HOME/bin:$LC_HOME/bin:${PATH:-}"
# Connect to the license server already running in this container.
export LM_LICENSE_FILE="${LM_LICENSE_FILE:-27000@localhost}"
export SNPSLMD_LICENSE_FILE="${SNPSLMD_LICENSE_FILE:-$LM_LICENSE_FILE}"
export FFT_PYTHON="${FFT_PYTHON:-$FFT_CONTAINER_SHARE/runtime/python/bin/python3}"
export FFT_TOOLS_PREFIX="${FFT_TOOLS_PREFIX:-$FFT_CONTAINER_SHARE/runtime/tools}"
