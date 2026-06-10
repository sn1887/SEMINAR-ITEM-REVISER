#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SLURM_SUBMIT_DIR:-${SCRIPT_DIR}/..}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
cd "$REPO_ROOT"

if [ -f "$HOME/.bashrc" ]; then
  # shellcheck source=/dev/null
  source "$HOME/.bashrc"
fi

CONDA_SH="${HOME}/miniconda3/etc/profile.d/conda.sh"
if [ -f "$CONDA_SH" ]; then
  # shellcheck source=/dev/null
  source "$CONDA_SH"
fi

if command -v conda >/dev/null 2>&1; then
  conda activate sn-item-reviser
else
  echo "Conda not found in PATH. Please load conda and activate sn-item-reviser first."
  exit 1
fi

export MLFLOW_TRACKING_URI="file:///dss/dsshome1/05/ra92lid2/SEMINAR-ITEM-REVISER/mlruns"
export MLFLOW_ALLOW_FILE_STORE=true

PHASE="${1:-smoke}"
shift || true
MODEL_ROOT="/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models"
BENCHMARK_SCRIPT="${REPO_ROOT}/scripts/benchmark_models.py"

if [[ ! -f "$BENCHMARK_SCRIPT" ]]; then
  echo "Benchmark runner not found: $BENCHMARK_SCRIPT"
  exit 1
fi

DEFAULT_ATTEMPTS="${BENCHMARK_ATTEMPTS:-1}"
DEFAULT_TIMEOUT="${BENCHMARK_TIMEOUT:-}"

if [[ -z "$DEFAULT_TIMEOUT" ]]; then
  case "$PHASE" in
    smoke)
      DEFAULT_TIMEOUT=1800
      ;;
    shortlist-5)
      DEFAULT_TIMEOUT=3600
      ;;
    shortlist-20)
      DEFAULT_TIMEOUT=7200
      ;;
    full-200)
      DEFAULT_TIMEOUT=43200
      ;;
    vision-20)
      DEFAULT_TIMEOUT=10800
      ;;
    all)
      echo "Phase 'all' should be submitted as separate Slurm jobs per phase to keep walltime realistic."
      exit 2
      ;;
    *)
      echo "Unknown benchmark phase: $PHASE"
      exit 2
      ;;
  esac
fi

HAS_ATTEMPTS=false
HAS_TIMEOUT=false
for arg in "$@"; do
  case "$arg" in
    --attempts|--attempts=*)
      HAS_ATTEMPTS=true
      ;;
    --timeout|--timeout=*)
      HAS_TIMEOUT=true
      ;;
  esac
done

FORWARD_ARGS=("$@")
if [[ "$HAS_ATTEMPTS" == false ]]; then
  FORWARD_ARGS+=(--attempts "$DEFAULT_ATTEMPTS")
fi
if [[ "$HAS_TIMEOUT" == false ]]; then
  FORWARD_ARGS+=(--timeout "$DEFAULT_TIMEOUT")
fi

python "$BENCHMARK_SCRIPT" --phase "$PHASE" --model-root "$MODEL_ROOT" "${FORWARD_ARGS[@]}"
