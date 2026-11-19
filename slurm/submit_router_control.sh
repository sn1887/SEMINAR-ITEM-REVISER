#!/usr/bin/env bash
# Submit the router-control runs (experiments/router_control_manifest.jsonl).
# Dry run by default; set DRY_RUN=0 to submit. One GPU job per run, all at once.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

DRY_RUN="${DRY_RUN:-1}"
PREFLIGHT="${PREFLIGHT:-1}"
METRIC_PREFLIGHT="${METRIC_PREFLIGHT:-1}"
METRIC_CACHE_PATH="${METRIC_CACHE_PATH:-.metric-cache}"
METRIC_OFFLINE="${METRIC_OFFLINE:-false}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
RUN_GROUP="${RUN_GROUP:-router_control_${RUN_TAG}}"
MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-seminar-item-reviser-router-control}"
PROGRESS_INTERVAL="${PROGRESS_INTERVAL:-10}"
TIME_LIMIT="${TIME_LIMIT:-04:00:00}"
SBATCH_SCRIPT="${REPO_ROOT}/slurm/router_control_run_single.sbatch"
SUBMISSION_ROOT="${REPO_ROOT}/outputs/${RUN_GROUP}/.submission_locks"

if [[ "$DRY_RUN" != "0" && "$DRY_RUN" != "1" ]]; then
  echo "DRY_RUN must be 0 or 1 (got $DRY_RUN)" >&2
  exit 2
fi
if [[ "$DRY_RUN" == "0" && -n "$(git status --short)" ]]; then
  echo "Refusing real submission from a dirty Git worktree:" >&2
  git status --short >&2
  exit 4
fi

CONDA_SH="${HOME}/miniconda3/etc/profile.d/conda.sh"
if [[ ! -f "$CONDA_SH" ]]; then
  echo "Conda profile script not found: $CONDA_SH" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$CONDA_SH"
conda activate sn-item-reviser

if [[ "$PREFLIGHT" == "1" ]]; then
  if [[ "$METRIC_PREFLIGHT" == "1" ]]; then
    python scripts/metric_cache_preflight.py --cache-path "$METRIC_CACHE_PATH"
  fi
  python scripts/build_shared_router_prompts.py --check
  python scripts/run_router_control.py validate
fi

echo "Router-control runs"
echo "Run group: $RUN_GROUP"
echo "Output root: ${REPO_ROOT}/outputs/${RUN_GROUP}"
echo "Git HEAD: $(git rev-parse HEAD)"
echo "Dry run: $DRY_RUN"

submitted=0
while IFS= read -r run_id; do
  output_dir="outputs/${RUN_GROUP}/${run_id}"
  export_args="ALL,RUN_GROUP=${RUN_GROUP},RUN_NAME=${run_id},HYDRA_OUTPUT_DIR=${output_dir},MLFLOW_EXPERIMENT_NAME=${MLFLOW_EXPERIMENT_NAME},PROGRESS_INTERVAL=${PROGRESS_INTERVAL},METRIC_CACHE_PATH=${METRIC_CACHE_PATH},METRIC_OFFLINE=${METRIC_OFFLINE}"
  command=(sbatch --job-name="$run_id" --time="$TIME_LIMIT" --export="$export_args" "$SBATCH_SCRIPT" "$run_id")

  if [[ "$DRY_RUN" == "1" ]]; then
    printf 'DRY RUN: '
    printf '%q ' "${command[@]}"
    printf '\n'
  else
    mkdir -p "$SUBMISSION_ROOT"
    lock_dir="${SUBMISSION_ROOT}/${run_id}.lock"
    if ! mkdir "$lock_dir" 2>/dev/null; then
      echo "Refusing duplicate submission for ${run_id} in ${RUN_GROUP}; lock exists: ${lock_dir}" >&2
      exit 3
    fi
    if [[ -e "${REPO_ROOT}/${output_dir}/metrics.json" ]]; then
      rmdir "$lock_dir"
      echo "Refusing duplicate completed run: ${output_dir}/metrics.json" >&2
      exit 3
    fi
    if ! "${command[@]}"; then
      rmdir "$lock_dir"
      exit 1
    fi
  fi
  submitted=$((submitted + 1))
done < <(python -c '
import json, sys
for line in open("experiments/router_control_manifest.jsonl", encoding="utf-8"):
    if line.strip():
        print(json.loads(line)["run_id"])
')

echo "Runs processed: $submitted"
