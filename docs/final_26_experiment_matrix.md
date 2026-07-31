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

P0 remains zero-shot and example-free. Before the final experiment freeze, its
taxonomy definitions, pairwise boundaries, evidence gate, clean-item preservation,
minimal-revision rules, and orchestration role contracts were clarified across all 16
labels. These changes make P0 a stronger final control than the earlier interim prompt;
the final v4 runs must therefore be compared within this frozen matrix rather than
treated as direct continuations of the earlier prompt version.

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
| Baseline checker / reviser | 4 / 4 |
| Orchestration router / fallback | 5 / 3 |
| Response-options / questionnaire-format specialist | 5 / 2 |
| Validator | 5 |
| Planner / wording / construct / bias | 0 each; P0 reused |

The 28 examples directly exercise all seven response-option/scale labels:
`agree_disagree_scale`, `unbalanced_scale`, `incomplete_options`,
`non_exclusive_options`, `missing_scale_labels`, `too_many_scale_points`, and
`polarity_mismatch`. They also exercise `open_closed_mismatch`, clean-item
preservation, routing, fallback restraint, and validation decisions. The remaining
eight taxonomy labels have no direct P2 example; improvements for them reflect the
zero-shot rules or model generalization rather than a direct in-context-example effect.
The per-role boundaries are recorded in `prompts/agents/README.md`.

The revised prompts are longer than the interim versions, especially for the P2
baseline reviser, response-options specialist, and validator. Run the documented GPU
preflight before submitting the full matrix and retain measured runtime rather than
assuming the interim per-item timing.

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
