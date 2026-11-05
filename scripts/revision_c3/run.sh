#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
RESULTS_DIR="${RESULTS_DIR:-$REPO_ROOT/results/revision_c3}"
GPU_RESULTS_DIR="${GPU_RESULTS_DIR:-$RESULTS_DIR/gpu}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
stage="${1:-all}"
if (( $# )); then shift; fi
mkdir -p "$RESULTS_DIR"
exec 9>"$RESULTS_DIR/.run.lock"
flock -n 9 || { echo "Another C3 wrapper job is active for this output directory." >&2; exit 1; }
cpu_audits() {
  if "$PYTHON" -c 'import json,sys; sys.exit(json.load(open(sys.argv[1]))["status"]!="complete")' "$RESULTS_DIR/cpu_complete.json"; then
    "$PYTHON" "$SCRIPT_DIR/audit_native_budgets.py" --results "$RESULTS_DIR"
    "$PYTHON" "$SCRIPT_DIR/build_case_audit.py" --results "$RESULTS_DIR"
  fi
}
case "$stage" in
  cpu) "$PYTHON" "$SCRIPT_DIR/run_cpu.py" --out "$RESULTS_DIR" "$@"; cpu_audits ;;
  gpu) "$PYTHON" "$SCRIPT_DIR/run_gpu.py" --cpu-results "$RESULTS_DIR" --out "$GPU_RESULTS_DIR" "$@" ;;
  all)
    "$PYTHON" "$SCRIPT_DIR/run_cpu.py" --out "$RESULTS_DIR"
    cpu_audits
    "$PYTHON" "$SCRIPT_DIR/run_gpu.py" --cpu-results "$RESULTS_DIR" --out "$GPU_RESULTS_DIR" "$@"
    ;;
  export) "$PYTHON" "$SCRIPT_DIR/export_results.py" --results "$RESULTS_DIR" --gpu-results "$GPU_RESULTS_DIR" "$@"; exit ;;
  *) echo "Usage: bash scripts/revision_c3/run.sh {cpu|gpu|all|export} [stage arguments]" >&2; exit 2 ;;
esac
"$PYTHON" "$SCRIPT_DIR/export_results.py" --results "$RESULTS_DIR" --gpu-results "$GPU_RESULTS_DIR"
