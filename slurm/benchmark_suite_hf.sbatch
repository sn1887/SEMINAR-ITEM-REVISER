#!/bin/bash
#SBATCH --job-name=item-reviser-bench
#SBATCH --partition=lrz-hgx-h100-94x4
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --output=logs/benchmark_%j.out
#SBATCH --error=logs/benchmark_%j.err

set -euo pipefail
mkdir -p logs

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
else
  echo "Conda profile script not found at $CONDA_SH"
  exit 1
fi

if ! command -v conda >/dev/null 2>&1; then
  echo "conda not available after sourcing activation scripts."
  exit 1
fi

conda activate sn-item-reviser

export MLFLOW_TRACKING_URI="file:///dss/dsshome1/05/ra92lid2/SEMINAR-ITEM-REVISER/mlruns"

PHASE="${1:-all}"
BENCHMARK_SCRIPT="${REPO_ROOT}/scripts/run_benchmark_suite.sh"

if [[ ! -x "$BENCHMARK_SCRIPT" ]]; then
  echo "Benchmark script not found or not executable: $BENCHMARK_SCRIPT"
  exit 1
fi

bash "$BENCHMARK_SCRIPT" "$PHASE"
