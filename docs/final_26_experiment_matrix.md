# Final 26-run experiment matrix

`experiments/final_26_run_manifest.jsonl` is the machine-readable, frozen
definition of the final seminar experiment matrix. Every row uses the immutable
`data/final_gold_200_v4/final_gold_200_unique_v4.jsonl` benchmark through the
`data=final_gold_200_v4` Hydra option. It is not copied into run folders and is
never supplied to prompts as gold metadata.

| Block | Condition | Runs |
| --- | --- | ---: |
| A | P0 codebook controls: 3 models × 2 pipelines × 2 modes | 12 |
| B | Qwen P1 operational option/format rules: 2 pipelines × 2 modes | 4 |
| C | Qwen P2 targeted option/format calibration: 2 pipelines × 2 modes | 4 |
| D | Qwen P2 targeted calibration with thinking: 2 pipelines × 2 modes | 4 |
| E | Gemma P2 transfer: 2 pipelines × end-to-end | 2 |

The modes are only `end_to_end` and `oracle_revision`; `detection_only` is
deliberately excluded. Decoding is identical for every row (greedy,
`max_new_tokens=2048`, temperature `0.0`, top-p `1.0`, one beam). Thinking is
enabled only in block D. P0 selects `baseline_codebook` or
`orchestration_codebook`; P1 selects `baseline_p1` or `orchestration_p1`; P2
selects `baseline_p2` or `orchestration_p2`.

P0 remains zero-shot and example-free. Three narrow consistency repairs affect
the control: its loaded/completeness boundary no longer suppresses unrelated
independent labels; its orchestration router drops an unreachable severity
instruction because the router schema has no severity field; and its shared
validator makes `fixes_detected_issue` nullable/not applicable when no issue was
detected on the clean accept path. Taxonomy and revision rules otherwise remain
unchanged.

The known treatment configs are pipeline-specific. Baseline packs fail fast
when orchestration is enabled, and orchestration packs fail fast on the baseline
path. This protects the manifest treatment assignment from a silent
prompt/pipeline mismatch.

## P2 interpretation boundary

P2 is not a general few-shot treatment over all 16 taxonomy labels. It adds
fixed, independently authored demonstrations concentrated on response-option
and open/closed-format decisions:

| Role | Demonstrations |
| --- | ---: |
| Baseline checker / reviser | 3 / 3 |
| Orchestration router / fallback | 4 / 3 |
| Response-options / questionnaire-format specialist | 3 / 2 |
| Validator | 3 |
| Planner / wording / construct / bias | 0 each; P0 reused |

The examples directly exercise `agree_disagree_scale`, `incomplete_options`,
`non_exclusive_options`, `missing_scale_labels`, and
`open_closed_mismatch`, plus clean-item preservation and validation decisions.
The option categories `unbalanced_scale`, `too_many_scale_points`, and
`polarity_mismatch` have no direct P2 example. Improvements outside the
demonstrated categories may reflect P1 operational rules or model
generalization, not a direct in-context-example effect. The per-role boundaries
are recorded in `prompts/agents/README.md`.

## Validate without scheduling

Activate the seminar environment and run the static audit plus all 26 Hydra
compositions:

```bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate sn-item-reviser
python scripts/validate_final_26_manifest.py validate --check-hydra
```

The Slurm submitter is deliberately dry-run by default. It validates the
manifest, composes each selected Hydra row, checks all model paths, and prints
the exact `sbatch` commands without scheduling work:

```bash
DRY_RUN=1 slurm/submit_final_26_matrix.sh
DRY_RUN=1 BLOCKS=B,C slurm/submit_final_26_matrix.sh
```

To require cached metric resources on an offline Slurm node, first complete a
connected metric preflight, then set `METRIC_OFFLINE=true` for the dry run and
later submission. The runner fails before generation if the BERTScore checkpoint
or Evaluate SARI module is absent from `.metric-cache`.

The metric cache has its own preflight command. By default it populates the
cache in connected mode and then proves strict offline loading with a one-row
semantic smoke test:

```bash
python scripts/metric_cache_preflight.py --cache-path .metric-cache
python scripts/metric_cache_preflight.py --cache-path .metric-cache --offline-only
```

`slurm/submit_final_26_matrix.sh` runs this command during `PREFLIGHT=1` before
printing or submitting final-matrix jobs. Set `METRIC_PREFLIGHT=0` only when the
same cache has already passed this check in the active environment.

## Later submission

Only after reviewing the dry-run output, schedule a group with:

```bash
METRIC_OFFLINE=true DRY_RUN=0 RUN_GROUP=final_26_YYYYMMDD_HHMMSS \
  slurm/submit_final_26_matrix.sh
```

Real submission refuses a dirty Git worktree by default. For a debugging-only
run, set `ALLOW_DIRTY_GIT_FOR_DEBUG=1`; the submitter writes the dirty file list
to `outputs/$RUN_GROUP/git_dirty_status_at_submission.txt`, and MLflow records
`git.dirty=true` plus `git.dirty_allowed_for_debug=true`.

Each job gets an isolated Hydra output at `outputs/$RUN_GROUP/$RUN_ID` and a
matching file-based MLflow root at `mlruns/$RUN_GROUP`. The wrapper logs the
manifest run ID, block, prompt pack, pipeline, thinking state, v4 dataset
version, complete decoding settings, and the Git commit through Hydra/MLflow
parameters. For a fixed `RUN_GROUP`, persistent submission locks prevent a
second enqueue of the same `RUN_ID`; completed `metrics.json` files are also
refused. To make an intentional new attempt, choose a new `RUN_GROUP` rather
than deleting a lock or prior artifact.
