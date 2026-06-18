#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SLURM_SUBMIT_DIR:-${SCRIPT_DIR}/..}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
cd "$REPO_ROOT"

mkdir -p logs

RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
RUN_GROUP="${RUN_GROUP:-gold_resilient_${RUN_TAG}}"
SBATCH_SCRIPT="${REPO_ROOT}/slurm/gold_orchestration_single.sbatch"
MODEL_ROOT="/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models"

declare -A MODEL_PATHS=(
  [qwen35_9b]="${MODEL_ROOT}/Qwen3.5-9B"
  [llama31_8b]="${MODEL_ROOT}/Llama-3.1-8B-Instruct"
  [qwen25_7b]="${MODEL_ROOT}/Qwen2.5-7B-Instruct"
  [gemma2_9b]="${MODEL_ROOT}/gemma-2-9b-it"
  [mistral7b_v03]="${MODEL_ROOT}/Mistral-7B-Instruct-v0.3"
  [glm4_9b]="${MODEL_ROOT}/glm-4-9b-chat-hf"
)

MODEL_ORDER=(
  qwen35_9b
  llama31_8b
  qwen25_7b
  gemma2_9b
  mistral7b_v03
  glm4_9b
)

MODES=(
  baseline
  orchestrated
)

echo "Submitting gold-set model matrix with RUN_TAG=${RUN_TAG}"
echo "Run group: ${RUN_GROUP}"
echo "MLflow folder: ${REPO_ROOT}/mlruns/${RUN_GROUP}"
echo "Hydra output folder: ${REPO_ROOT}/outputs/${RUN_GROUP}"

for model_slug in "${MODEL_ORDER[@]}"; do
  model_path="${MODEL_PATHS[$model_slug]}"
  if [[ ! -d "$model_path" ]]; then
    echo "Model path not found for ${model_slug}: ${model_path}" >&2
    exit 1
  fi

  for mode in "${MODES[@]}"; do
    job_mode="$mode"
    job_name="gold-${model_slug}-${job_mode}"
    echo "Submitting ${job_name}"
    sbatch \
      --job-name="$job_name" \
      --export=ALL,RUN_TAG="$RUN_TAG",RUN_GROUP="$RUN_GROUP",MODEL_SLUG="$model_slug",MODEL_PATH="$model_path" \
      "$SBATCH_SCRIPT" "$job_mode"
  done
done
