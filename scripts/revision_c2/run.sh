#!/usr/bin/env bash
set -euo pipefail
REVISION_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REVISION_REPO_DIR="$(cd -- "${REVISION_SCRIPT_DIR}/../.." && pwd)"
cd "${REVISION_REPO_DIR}"
REVISION_PYTHON="${PYTHON:-${REVISION_REPO_DIR}/.venv/bin/python}"
REVISION_RESULTS="${RESULTS_DIR:-${REVISION_REPO_DIR}/results/revision_c2}"
REVISION_E2E="${E2E_RESULTS_DIR:-${REVISION_RESULTS}/e2e}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export TOKENIZERS_PARALLELISM=false
REVISION_STAGE="${1:-all}"
if [[ $# -gt 0 ]]; then shift; fi
mkdir -p "${REVISION_RESULTS}"
exec 9>"${REVISION_RESULTS}/.run.lock"
flock -n 9 || { echo 'Another revision_c2 run is active in this output directory.' >&2; exit 1; }
case "${REVISION_STAGE}" in
  cpu)
    "${REVISION_PYTHON}" scripts/revision_c2/run_cpu.py --out "${REVISION_RESULTS}" "$@"
    ;;
  gpu)
    "${REVISION_PYTHON}" scripts/revision_c2/run_e2e.py --cpu-results "${REVISION_RESULTS}" --out "${REVISION_E2E}" "$@"
    ;;
  all)
    "${REVISION_PYTHON}" -m unittest discover -s scripts/revision_c2 -p 'test_*.py'
    "${REVISION_PYTHON}" scripts/revision_c2/run_cpu.py --out "${REVISION_RESULTS}"
    "${REVISION_PYTHON}" scripts/revision_c2/run_e2e.py --cpu-results "${REVISION_RESULTS}" --out "${REVISION_E2E}" "$@"
    ;;
  export) ;;
  *) echo 'Usage: bash scripts/revision_c2/run.sh {cpu|gpu|all|export} [Python stage options]' >&2; exit 2 ;;
esac
"${REVISION_PYTHON}" scripts/revision_c2/export_results.py --results "${REVISION_RESULTS}" --e2e-results "${REVISION_E2E}"
