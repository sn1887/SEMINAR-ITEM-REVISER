# Seminar Item Reviser

This repository contains the final implementation for an LLM-based survey-item
quality checker and reviser. It evaluates whether a model can detect
questionnaire-design defects and produce conservative, construct-preserving
revisions.

The final submission is centered on:

- the canonical 200-item v4 benchmark in `data/final_gold_200_v4/`;
- Hydra configs for data, prompts, models, orchestration, and evaluation;
- baseline and orchestrated item-reviser pipelines;
- the frozen 26-run experiment manifest in `experiments/`;
- the final report source and PDF in `final-report/`.

## Repository Map

```text
seminar-item-reviser/
├── configs/              # Hydra configs for final runs
├── data/                 # Final v4 benchmark and tiny demo input
├── docs/                 # Design, evaluation, orchestration, and LRZ notes
├── experiments/          # Frozen final 26-run manifest
├── final-report/         # Report source, references, figures, and PDF
├── prompts/              # Final baseline/orchestration prompt packs
├── scripts/              # Evaluation and final-matrix entrypoints
├── slurm/                # Final matrix SLURM submitter
├── src/item_reviser/     # Python package
├── Makefile
├── pyproject.toml
└── README.md
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[hf]'
```

For local development without Hugging Face dependencies:

```bash
pip install -e '.[dev]'
```

## Smoke Check

```bash
python scripts/smoke_test.py
```

This runs the pipeline with a deterministic in-script fake model and checks the
control flow without loading a GPU model.

## Evaluate The Final V4 Benchmark

The default Hydra config now uses `data=final_gold_200_v4` and
`prompt=baseline_codebook`.

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL
```

Hydra writes outputs under `outputs/`, including:

```text
predictions.jsonl
metrics.json
dataset_metadata.json
report.md
```

For a short development run against the same final benchmark:

```bash
python scripts/evaluate.py experiment.max_items=20
```

## Prompt Packs

The final experiment uses six prompt packs:

- `baseline_codebook`
- `orchestration_codebook`
- `baseline_p1`
- `orchestration_p1`
- `baseline_p2`
- `orchestration_p2`

Baseline packs must run with `orchestration.enabled=false`. Orchestration packs
must run with `orchestration.enabled=true`; the pipeline rejects mismatched
prompt/runtime pairings before model construction.

Example baseline P2 run:

```bash
python scripts/evaluate.py \
  data=final_gold_200_v4 \
  prompt=baseline_p2 \
  orchestration.enabled=false \
  evaluator.mode=end_to_end
```

Example orchestrated P2 run:

```bash
python scripts/evaluate.py \
  data=final_gold_200_v4 \
  prompt=orchestration_p2 \
  orchestration.enabled=true \
  evaluator.mode=end_to_end
```

## Evaluation Modes

- `end_to_end`: detect issues and revise from predicted labels.
- `oracle_revision`: use gold labels as detected issues and evaluate revision
  quality independently of model detection.
- `detection_only`: run only the detector/router and skip revision.

Detection metrics include micro precision, recall, F1, exact label-set match,
and clean false-positive rate. Revision metrics include question BERTScore F1,
SARI, exact question/option diagnostics, and revision coverage metadata.

## Final 26-Run Matrix

Validate the frozen manifest and Hydra compositions:

```bash
python scripts/validate_final_26_manifest.py validate --check-hydra
```

Dry-run the SLURM submission plan:

```bash
DRY_RUN=1 slurm/submit_final_26_matrix.sh
```

Run the metric-cache preflight before offline LRZ jobs:

```bash
python scripts/metric_cache_preflight.py --cache-path .metric-cache
python scripts/metric_cache_preflight.py --cache-path .metric-cache --offline-only
```

See `docs/final_26_experiment_matrix.md` for the full matrix design and
submission workflow.
