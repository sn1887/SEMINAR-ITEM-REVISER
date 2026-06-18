#!/bin/bash
#SBATCH --job-name=gold-orch-single
#SBATCH --partition=lrz-hgx-h100-94x4
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

MODE="${1:-${ORCH_MODE:-baseline}}"
case "$MODE" in
  baseline)
    ORCH_ENABLED=false
    RUN_KIND=baseline
    ;;
  orchestrated)
    ORCH_ENABLED=true
    RUN_KIND=orchestrated
    ;;
  *)
    echo "Usage: sbatch slurm/gold_orchestration_single.sbatch [baseline|orchestrated]"
    exit 2
    ;;
esac

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

MODEL_PATH="${MODEL_PATH:-/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/Qwen3.5-9B}"
MODEL_SLUG="${MODEL_SLUG:-qwen35_9b}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
RUN_GROUP="${RUN_GROUP:-gold_resilient_${RUN_TAG}}"
PROGRESS_INTERVAL="${PROGRESS_INTERVAL:-25}"
RUN_NAME="${MODEL_SLUG}_gold1000_${RUN_KIND}_${RUN_TAG}"
HYDRA_OUTPUT_DIR="${HYDRA_OUTPUT_DIR:-outputs/${RUN_GROUP}/${MODEL_SLUG}_${RUN_KIND}}"

export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-file://${REPO_ROOT}/mlruns/${RUN_GROUP}}"
export MLFLOW_ALLOW_FILE_STORE="${MLFLOW_ALLOW_FILE_STORE:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

echo "Repository: ${REPO_ROOT}"
echo "Run group: ${RUN_GROUP}"
echo "Mode: ${MODE}"
echo "Orchestration enabled: ${ORCH_ENABLED}"
echo "Model path: ${MODEL_PATH}"
echo "Model slug: ${MODEL_SLUG}"
echo "Hydra output dir: ${HYDRA_OUTPUT_DIR}"
echo "MLflow tracking URI: ${MLFLOW_TRACKING_URI}"
echo "MLflow run name: ${RUN_NAME}"

python scripts/evaluate.py \
  experiment=item_reviser_eval \
  data=final_gold_1000 \
  model=hf_local \
  "model.model_path=${MODEL_PATH}" \
  model.decoding.method=greedy \
  tracking.enabled=true \
  "tracking.experiment_name=${RUN_GROUP}" \
  "tracking.log_progress_every_items=${PROGRESS_INTERVAL}" \
  "tracking.run_name=${RUN_NAME}" \
  "orchestration.enabled=${ORCH_ENABLED}" \
  "hydra.run.dir=${HYDRA_OUTPUT_DIR}"
