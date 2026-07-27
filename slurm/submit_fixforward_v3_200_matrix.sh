#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SLURM_SUBMIT_DIR:-${SCRIPT_DIR}/..}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
cd "$REPO_ROOT"

mkdir -p logs

RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
RUN_GROUP="${RUN_GROUP:-fixforward_v3_200_${RUN_TAG}}"
MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-seminar-item-reviser-v3-fixforward-200}"
PROGRESS_INTERVAL="${PROGRESS_INTERVAL:-10}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-1024}"
DRY_RUN="${DRY_RUN:-0}"
SBATCH_SCRIPT="${REPO_ROOT}/slurm/fixforward_v3_200_single.sbatch"
MODEL_ROOT="/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models"

declare -A MODEL_PATHS=(
  [mistral7b_v03]="${MODEL_ROOT}/Mistral-7B-Instruct-v0.3"
  [gemma2_9b]="${MODEL_ROOT}/gemma-2-9b-it"
  [qwen35_9b]="${MODEL_ROOT}/Qwen3.5-9B"
)

MODEL_ORDER=(
  mistral7b_v03
  gemma2_9b
  qwen35_9b
)

PIPELINE_MODES=(
  baseline
  orchestrated
)

EVALUATOR_MODES=(
  end_to_end
  detection_only
  oracle_revision
)

if [[ ! -f "$SBATCH_SCRIPT" ]]; then
  echo "SBATCH script not found: $SBATCH_SCRIPT" >&2
  exit 1
fi

echo "Submitting fix-forward v3 200-item matrix"
echo "Run tag: ${RUN_TAG}"
echo "Run group/folder: ${RUN_GROUP}"
echo "MLflow folder: ${REPO_ROOT}/mlruns/${RUN_GROUP}"
echo "MLflow experiment name: ${MLFLOW_EXPERIMENT_NAME}"
echo "Hydra output folder: ${REPO_ROOT}/outputs/${RUN_GROUP}"
echo "Max new tokens: ${MAX_NEW_TOKENS}"
echo "Progress interval: ${PROGRESS_INTERVAL}"
echo "Dry run: ${DRY_RUN}"

submitted=0
for model_slug in "${MODEL_ORDER[@]}"; do
  model_path="${MODEL_PATHS[$model_slug]}"
  if [[ ! -d "$model_path" ]]; then
    echo "Model path not found for ${model_slug}: ${model_path}" >&2
    exit 1
  fi

  for evaluator_mode in "${EVALUATOR_MODES[@]}"; do
    for pipeline_mode in "${PIPELINE_MODES[@]}"; do
      job_name="v3-${model_slug}-${pipeline_mode}-${evaluator_mode}"
      export_args=(
        "ALL"
        "RUN_TAG=${RUN_TAG}"
        "RUN_GROUP=${RUN_GROUP}"
        "MLFLOW_EXPERIMENT_NAME=${MLFLOW_EXPERIMENT_NAME}"
        "MODEL_SLUG=${model_slug}"
        "MODEL_PATH=${model_path}"
        "PROGRESS_INTERVAL=${PROGRESS_INTERVAL}"
        "MAX_NEW_TOKENS=${MAX_NEW_TOKENS}"
      )
      export_arg="$(IFS=,; echo "${export_args[*]}")"

      echo "Submitting ${job_name}"
      if [[ "$DRY_RUN" == "1" ]]; then
        printf 'sbatch --job-name=%q --export=%q %q %q %q\n' \
          "$job_name" "$export_arg" "$SBATCH_SCRIPT" "$pipeline_mode" "$evaluator_mode"
      else
        sbatch \
          --job-name="$job_name" \
          --export="$export_arg" \
          "$SBATCH_SCRIPT" "$pipeline_mode" "$evaluator_mode"
      fi
      submitted=$((submitted + 1))
    done
  done
done

echo "Matrix jobs processed: ${submitted}"
