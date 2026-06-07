#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
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

PHASE="${1:-all}"
shift || true
MODEL_ROOT="/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models"
BENCHMARK_SCRIPT="${REPO_ROOT}/scripts/benchmark_models.py"

if [[ ! -f "$BENCHMARK_SCRIPT" ]]; then
  echo "Benchmark runner not found: $BENCHMARK_SCRIPT"
  exit 1
fi

python "$BENCHMARK_SCRIPT" --phase "$PHASE" --model-root "$MODEL_ROOT" "$@"
