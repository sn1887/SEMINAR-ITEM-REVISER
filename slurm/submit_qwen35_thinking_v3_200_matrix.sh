#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SLURM_SUBMIT_DIR:-${SCRIPT_DIR}/..}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
cd "$REPO_ROOT"

mkdir -p logs

RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
RUN_GROUP="${RUN_GROUP:-qwen35_thinking_v3_200_${RUN_TAG}}"
MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-seminar-item-reviser-v3-qwen35-thinking}"
PROGRESS_INTERVAL="${PROGRESS_INTERVAL:-10}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"
DRY_RUN="${DRY_RUN:-0}"
SBATCH_SCRIPT="${REPO_ROOT}/slurm/qwen35_thinking_v3_200_single.sbatch"
MODEL_PATH="/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/Qwen3.5-9B"
MODEL_SLUG="qwen35_9b"

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

if [[ ! -d "$MODEL_PATH" ]]; then
  echo "Model path not found: $MODEL_PATH" >&2
  exit 1
fi

echo "Submitting Qwen3.5-9B thinking-mode v3 200-item matrix"
echo "Run tag: ${RUN_TAG}"
echo "Run group/folder: ${RUN_GROUP}"
echo "MLflow folder: ${REPO_ROOT}/mlruns/${RUN_GROUP}"
echo "MLflow experiment name: ${MLFLOW_EXPERIMENT_NAME}"
echo "Hydra output folder: ${REPO_ROOT}/outputs/${RUN_GROUP}"
echo "Max new tokens: ${MAX_NEW_TOKENS}"
echo "Progress interval: ${PROGRESS_INTERVAL}"
echo "Dry run: ${DRY_RUN}"

submitted=0
for evaluator_mode in "${EVALUATOR_MODES[@]}"; do
  for pipeline_mode in "${PIPELINE_MODES[@]}"; do
    if [[ "$pipeline_mode" == "baseline" ]]; then
      time_limit="04:00:00"
    else
      time_limit="06:00:00"
    fi

    job_name="qwen35-thinking-${pipeline_mode}-${evaluator_mode}"
    export_args=(
      "ALL"
      "RUN_TAG=${RUN_TAG}"
      "RUN_GROUP=${RUN_GROUP}"
      "MLFLOW_EXPERIMENT_NAME=${MLFLOW_EXPERIMENT_NAME}"
      "MODEL_SLUG=${MODEL_SLUG}"
      "MODEL_PATH=${MODEL_PATH}"
      "PROGRESS_INTERVAL=${PROGRESS_INTERVAL}"
      "MAX_NEW_TOKENS=${MAX_NEW_TOKENS}"
    )
    export_arg="$(IFS=,; echo "${export_args[*]}")"

    echo "Submitting ${job_name} with --time=${time_limit}"
    if [[ "$DRY_RUN" == "1" ]]; then
      printf 'sbatch --job-name=%q --time=%q --export=%q %q %q %q\n' \
        "$job_name" "$time_limit" "$export_arg" "$SBATCH_SCRIPT" "$pipeline_mode" "$evaluator_mode"
    else
      sbatch \
        --job-name="$job_name" \
        --time="$time_limit" \
        --export="$export_arg" \
        "$SBATCH_SCRIPT" "$pipeline_mode" "$evaluator_mode"
    fi
    submitted=$((submitted + 1))
  done
done

echo "Thinking-mode jobs processed: ${submitted}"
