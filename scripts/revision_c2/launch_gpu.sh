#!/usr/bin/env bash
set -euo pipefail
REVISION_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REVISION_REPO_DIR="$(cd -- "${REVISION_SCRIPT_DIR}/../.." && pwd)"
cd "${REVISION_REPO_DIR}"
REVISION_RESULTS="${RESULTS_DIR:-${REVISION_REPO_DIR}/results/revision_c2}"
mkdir -p "${REVISION_RESULTS}"
# flock in run.sh prevents concurrent jobs from sharing one result directory.
if [[ -f "${REVISION_RESULTS}/gpu.pid" ]]; then
  read -r REVISION_OLD_PID < "${REVISION_RESULTS}/gpu.pid"
  if kill -0 "${REVISION_OLD_PID}" 2>/dev/null; then
    echo "Recorded process ${REVISION_OLD_PID} still exists; inspect it before launching again." >&2
    exit 1
  fi
fi
REVISION_LOG="${REVISION_RESULTS}/gpu_$(date +%Y%m%d_%H%M%S).log"
nohup bash scripts/revision_c2/run.sh gpu "$@" > "${REVISION_LOG}" 2>&1 < /dev/null &
REVISION_PID=$!
echo "${REVISION_PID}" > "${REVISION_RESULTS}/gpu.pid"
echo "${REVISION_LOG}" > "${REVISION_RESULTS}/gpu_log_path.txt"
echo "Started PID ${REVISION_PID}"
echo "Log: ${REVISION_LOG}"
