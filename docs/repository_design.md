# Repository Design

## Purpose

This repository implements an advanced but manageable solo project for the seminar task: an **Item Reviser Agent** for survey questionnaire items.

The design supports three phases:

1. **Agent prototype**: LLM-backed quality checking and revision.
2. **Benchmark phase**: compare multiple local LRZ models on the same gold evaluation set.
3. **Audit phase**: manually review model outputs and taxonomy boundaries.

## Research-repository principles

The repo follows a configuration-first research workflow inspired by large lab ML repositories:

- Every experiment is launched through Hydra config.
- All hyperparameters, model paths, data paths, prompt choices, and agent choices are declared in YAML.
- Scripts are thin entrypoints; research logic lives in `src/item_reviser`.
- Outputs are written to timestamped experiment directories.
- The dataset schema is explicit and versionable.
- Evaluation metrics are saved as JSON and Markdown.

## Main components

```text
src/item_reviser/
├── agents/       # Agent classes: quality checker, reviser, pipeline controller
├── evaluation/   # Dataset loading, metrics, report generation
├── models/       # HF local and OpenAI-compatible model backends
├── prompting.py  # Prompt-template loading and rendering
├── schemas.py    # Typed dataclasses for items, checks, revisions
└── utils.py      # Small utilities
```

## Why this is suitable for the seminar

The seminar pipeline contains a single item generator, several error checkers,
and an item reviser. This repository focuses on the implemented
quality-checking and item-revision loop used in the final evaluation.

## Why Hydra

Hydra makes it easy to run:

```bash
python scripts/evaluate.py model=hf_local model.model_path=/path/to/model
python scripts/evaluate.py model=hf_local model.decoding.method=sampling model.decoding.temperature=0.7
python scripts/evaluate.py data=final_gold_200_v4 prompt=baseline_p2
```

This is useful because model choice, decoding, and prompt versions should remain
experimental variables, not code edits.

## Prompt registry

The active prompt registry is declared under `configs/prompt/`. Prompt bodies
stay in Markdown files under `prompts/agents/`. The final baseline prompt packs
provide the quality-checker and item-reviser roles; the orchestrated prompt packs
provide the router, planner, specialists, fallback reviser, and validator. Config
controls template paths, retry count, and timeout per agent. This keeps prompts
easy to edit and ensures Hydra records the prompt setup in every run directory.
