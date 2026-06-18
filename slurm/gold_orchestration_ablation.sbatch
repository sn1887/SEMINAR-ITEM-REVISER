#!/bin/bash
#SBATCH --job-name=gold-orch-ablation
#SBATCH --partition=lrz-hgx-h100-94x4
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --output=logs/gold_orch_ablation_%j.out
#SBATCH --error=logs/gold_orch_ablation_%j.err

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SLURM_SUBMIT_DIR:-${SCRIPT_DIR}/..}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
cd "$REPO_ROOT"

mkdir -p logs

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

export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-file://${REPO_ROOT}/mlruns}"
export MLFLOW_ALLOW_FILE_STORE="${MLFLOW_ALLOW_FILE_STORE:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

MODEL_PATH="${MODEL_PATH:-/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/Qwen3.5-9B}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
PROGRESS_INTERVAL="${PROGRESS_INTERVAL:-25}"

COMMON_OVERRIDES=(
  experiment=item_reviser_eval
  data=final_gold_1000
  model=hf_local
  "model.model_path=${MODEL_PATH}"
  model.decoding.method=greedy
  tracking.enabled=true
  "tracking.log_progress_every_items=${PROGRESS_INTERVAL}"
)

echo "Repository: ${REPO_ROOT}"
echo "Model path: ${MODEL_PATH}"
echo "MLflow tracking URI: ${MLFLOW_TRACKING_URI}"
echo "Run tag: ${RUN_TAG}"
echo "Starting baseline gold-1000 evaluation with orchestration disabled."

python scripts/evaluate.py \
  "${COMMON_OVERRIDES[@]}" \
  orchestration.enabled=false \
  "tracking.run_name=qwen35_9b_gold1000_baseline_${RUN_TAG}"

echo "Baseline evaluation finished."
echo "Starting orchestrated gold-1000 evaluation with orchestration enabled."

python scripts/evaluate.py \
  "${COMMON_OVERRIDES[@]}" \
  orchestration.enabled=true \
  "tracking.run_name=qwen35_9b_gold1000_orchestrated_${RUN_TAG}"

echo "Gold orchestration ablation finished."
