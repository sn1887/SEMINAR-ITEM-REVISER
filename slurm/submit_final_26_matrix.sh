#!/usr/bin/env bash
# Submit the frozen final 26-run matrix.  Set DRY_RUN=1 to print only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SLURM_SUBMIT_DIR:-${SCRIPT_DIR}/..}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
cd "$REPO_ROOT"

DRY_RUN="${DRY_RUN:-1}"
PREFLIGHT="${PREFLIGHT:-1}"
METRIC_PREFLIGHT="${METRIC_PREFLIGHT:-1}"
METRIC_CACHE_PATH="${METRIC_CACHE_PATH:-.metric-cache}"
METRIC_OFFLINE="${METRIC_OFFLINE:-false}"
ALLOW_DIRTY_GIT_FOR_DEBUG="${ALLOW_DIRTY_GIT_FOR_DEBUG:-0}"
BLOCKS="${BLOCKS:-A,B,C,D,E}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
RUN_GROUP="${RUN_GROUP:-final_26_${RUN_TAG}}"
MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-seminar-item-reviser-final-26}"
PROGRESS_INTERVAL="${PROGRESS_INTERVAL:-10}"
SBATCH_SCRIPT="${REPO_ROOT}/slurm/final_26_run_single.sbatch"
SUBMISSION_ROOT="${REPO_ROOT}/outputs/${RUN_GROUP}/.submission_locks"

if [[ ! -f "$SBATCH_SCRIPT" ]]; then
  echo "SBATCH script not found: $SBATCH_SCRIPT" >&2
  exit 1
fi
if [[ "$DRY_RUN" != "0" && "$DRY_RUN" != "1" ]]; then
  echo "DRY_RUN must be 0 or 1 (got $DRY_RUN)" >&2
  exit 2
fi
if [[ "$ALLOW_DIRTY_GIT_FOR_DEBUG" != "0" && "$ALLOW_DIRTY_GIT_FOR_DEBUG" != "1" ]]; then
  echo "ALLOW_DIRTY_GIT_FOR_DEBUG must be 0 or 1 (got $ALLOW_DIRTY_GIT_FOR_DEBUG)" >&2
  exit 2
fi

if [[ "$DRY_RUN" == "0" ]]; then
  git_dirty="$(git status --short || true)"
  if [[ -n "$git_dirty" && "$ALLOW_DIRTY_GIT_FOR_DEBUG" != "1" ]]; then
    echo "Refusing real final-matrix submission from a dirty Git worktree." >&2
    echo "Commit/stash changes first, or set ALLOW_DIRTY_GIT_FOR_DEBUG=1 for an explicit debugging run." >&2
    echo "$git_dirty" >&2
    exit 4
  fi
  if [[ -n "$git_dirty" ]]; then
    mkdir -p "${REPO_ROOT}/outputs/${RUN_GROUP}"
    dirty_log="${REPO_ROOT}/outputs/${RUN_GROUP}/git_dirty_status_at_submission.txt"
    {
      echo "Dirty Git worktree allowed for debugging at $(date -Is)."
      echo
      echo "$git_dirty"
    } > "$dirty_log"
    echo "WARNING: dirty Git worktree allowed for debugging; status logged to $dirty_log" >&2
  fi
fi

if [[ "$PREFLIGHT" == "1" ]]; then
  CONDA_SH="${HOME}/miniconda3/etc/profile.d/conda.sh"
  if [[ ! -f "$CONDA_SH" ]]; then
    echo "Conda profile script not found: $CONDA_SH" >&2
    exit 1
  fi
  # shellcheck source=/dev/null
  source "$CONDA_SH"
  conda activate sn-item-reviser
  if [[ "$METRIC_PREFLIGHT" == "1" ]]; then
    python scripts/metric_cache_preflight.py --cache-path "$METRIC_CACHE_PATH"
  fi
  python scripts/validate_final_26_manifest.py validate --blocks "$BLOCKS" --check-hydra
fi

echo "Final 26-run matrix"
echo "Blocks: $BLOCKS"
echo "Run group: $RUN_GROUP"
echo "MLflow root: ${REPO_ROOT}/mlruns/${RUN_GROUP}"
echo "Output root: ${REPO_ROOT}/outputs/${RUN_GROUP}"
echo "Dry run: $DRY_RUN"
echo "Metric cache: $METRIC_CACHE_PATH"
echo "Metric offline override: $METRIC_OFFLINE"

submitted=0
while IFS= read -r row; do
  readarray -t fields < <(python -c '
import json, sys
row = json.loads(sys.stdin.read())
print(row["run_id"])
print(row["model_path"])
print(row["pipeline"])
' <<<"$row")
  run_id="${fields[0]}"
  model_path="${fields[1]}"
  pipeline="${fields[2]}"
  if [[ ! -d "$model_path" ]]; then
    echo "Model path unavailable for $run_id: $model_path" >&2
    exit 1
  fi
  if [[ "$pipeline" == "baseline" ]]; then
    time_limit="04:00:00"
  else
    time_limit="06:00:00"
  fi
  run_name="$run_id"
  output_dir="outputs/${RUN_GROUP}/${run_name}"
  export_args="ALL,RUN_GROUP=${RUN_GROUP},RUN_NAME=${run_name},HYDRA_OUTPUT_DIR=${output_dir},MLFLOW_EXPERIMENT_NAME=${MLFLOW_EXPERIMENT_NAME},PROGRESS_INTERVAL=${PROGRESS_INTERVAL},METRIC_CACHE_PATH=${METRIC_CACHE_PATH},METRIC_OFFLINE=${METRIC_OFFLINE},ALLOW_DIRTY_GIT_FOR_DEBUG=${ALLOW_DIRTY_GIT_FOR_DEBUG}"
  command=(sbatch --job-name="$run_id" --time="$time_limit" --export="$export_args" "$SBATCH_SCRIPT" "$run_id")

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
done < <(python scripts/validate_final_26_manifest.py list --blocks "$BLOCKS")

echo "Runs processed: $submitted"
