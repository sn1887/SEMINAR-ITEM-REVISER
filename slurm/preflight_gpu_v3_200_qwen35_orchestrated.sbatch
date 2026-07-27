#!/bin/bash
#SBATCH --job-name=v3-gpu-preflight-qwen35
#SBATCH --partition=lrz-hgx-h100-94x4
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

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

RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
RUN_GROUP="${RUN_GROUP:-gpu_preflight_v3_200_${RUN_TAG}}"
RUN_NAME="${RUN_NAME:-qwen35_9b_orchestrated_end_to_end_max5_gpu_preflight_${RUN_TAG}}"
HYDRA_OUTPUT_DIR="${HYDRA_OUTPUT_DIR:-outputs/${RUN_GROUP}/${RUN_NAME}}"
MODEL_PATH="${MODEL_PATH:-/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/Qwen3.5-9B}"
MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-seminar-item-reviser-v3-gpu-preflight}"
MAX_ITEMS="${MAX_ITEMS:-5}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-1024}"
PROGRESS_INTERVAL="${PROGRESS_INTERVAL:-1}"

export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-file://${REPO_ROOT}/mlruns/${RUN_GROUP}}"
export MLFLOW_ALLOW_FILE_STORE="${MLFLOW_ALLOW_FILE_STORE:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export HYDRA_FULL_ERROR="${HYDRA_FULL_ERROR:-1}"

echo "Repository: ${REPO_ROOT}"
echo "Git HEAD: $(git rev-parse --short HEAD 2>/dev/null || echo unavailable)"
echo "Git dirty files:"
git status --short || true
echo "Run group: ${RUN_GROUP}"
echo "MLflow tracking URI: ${MLFLOW_TRACKING_URI}"
echo "MLflow experiment: ${MLFLOW_EXPERIMENT_NAME}"
echo "Run name: ${RUN_NAME}"
echo "Hydra output dir: ${HYDRA_OUTPUT_DIR}"
echo "Model path: ${MODEL_PATH}"
echo "Max items: ${MAX_ITEMS}"
echo "Max new tokens: ${MAX_NEW_TOKENS}"

python scripts/evaluate.py \
  experiment=item_reviser_eval \
  experiment.max_items="${MAX_ITEMS}" \
  data=final_gold_200_v3_pure_loaded \
  model=hf_local \
  "model.model_path=${MODEL_PATH}" \
  "model.chat_template.enable_thinking=false" \
  "model.decoding.method=greedy" \
  "model.decoding.temperature=0.0" \
  "model.decoding.top_p=1.0" \
  "model.decoding.max_new_tokens=${MAX_NEW_TOKENS}" \
  prompt=orchestration_codebook \
  orchestration.enabled=true \
  evaluator.mode=end_to_end \
  evaluator.continue_on_item_error=true \
  evaluator.write_predictions_incrementally=true \
  evaluator.include_gold=false \
  tracking.enabled=true \
  "tracking.experiment_name=${MLFLOW_EXPERIMENT_NAME}" \
  "tracking.log_progress_every_items=${PROGRESS_INTERVAL}" \
  "tracking.run_name=${RUN_NAME}" \
  "hydra.run.dir=${HYDRA_OUTPUT_DIR}"
