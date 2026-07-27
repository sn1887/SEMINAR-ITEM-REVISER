#!/bin/bash
#SBATCH --job-name=seminar-final-26
#SBATCH --partition=lrz-hgx-h100-94x4
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

RUN_ID="${1:?Usage: sbatch final_26_run_single.sbatch RUN_ID}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SLURM_SUBMIT_DIR:-${SCRIPT_DIR}/..}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
cd "$REPO_ROOT"
mkdir -p logs

CONDA_SH="${HOME}/miniconda3/etc/profile.d/conda.sh"
if [[ ! -f "$CONDA_SH" ]]; then
  echo "Conda profile script not found: $CONDA_SH" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$CONDA_SH"
conda activate sn-item-reviser

export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export HYDRA_FULL_ERROR="${HYDRA_FULL_ERROR:-1}"
export RUN_NAME="${RUN_NAME:-${RUN_ID}}"
export HYDRA_OUTPUT_DIR="${HYDRA_OUTPUT_DIR:-outputs/${RUN_GROUP:?RUN_GROUP is required}/${RUN_NAME}}"
export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-file://${REPO_ROOT}/mlruns/${RUN_GROUP}}"
export MLFLOW_ALLOW_FILE_STORE="${MLFLOW_ALLOW_FILE_STORE:-true}"

echo "Repository: $REPO_ROOT"
echo "Run ID: $RUN_ID"
echo "Run group: ${RUN_GROUP}"
echo "Run name: ${RUN_NAME}"
echo "Hydra output: ${HYDRA_OUTPUT_DIR}"
echo "MLflow URI: ${MLFLOW_TRACKING_URI}"
echo "Git HEAD: $(git rev-parse HEAD 2>/dev/null || echo unavailable)"

python scripts/run_final_26_experiment.py --run-id "$RUN_ID"
