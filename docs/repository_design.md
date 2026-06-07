# Repository Design

## Purpose

This repository implements an advanced but manageable solo project for the seminar task: an **Item Reviser Agent** for survey questionnaire items.

The design supports three phases:

1. **Prototype**: rule-based checks and deterministic mock backend.
2. **Agent phase**: LLM-backed quality checking and revision.
3. **Benchmark phase**: compare multiple local LRZ models on the same 200-item evaluation set.

## Research-repository principles

The repo follows a configuration-first research workflow inspired by large lab ML repositories:

- Every experiment is launched through Hydra config.
- All hyperparameters, model paths, data paths, and agent choices are declared in YAML.
- Scripts are thin entrypoints; research logic lives in `src/item_reviser`.
- Outputs are written to timestamped experiment directories.
- There is a mock backend so the repo can be tested without GPUs.
- The dataset schema is explicit and versionable.
- Evaluation metrics are saved as JSON and Markdown.

## Main components

```text
src/item_reviser/
├── agents/       # Agent classes: quality checker, reviser, pipeline controller
├── checks/       # Rule-based baseline checks for wording and scale problems
├── evaluation/   # Dataset loading, metrics, report generation
├── models/       # Mock, HF local, OpenAI-compatible model backends
├── schemas.py    # Typed dataclasses for items, checks, revisions
└── utils.py      # Small utilities
```

## Why this is suitable for the seminar

The seminar pipeline contains a single item generator, several error checkers, and an item reviser. This repository focuses on the quality-checking and item-revision loop, but it includes stubs for earlier pipeline components so that the item reviser can later be integrated into the full pipeline.

## Why Hydra

Hydra makes it easy to run:

```bash
python scripts/evaluate.py model=mock
python scripts/evaluate.py model=hf_local model.model_path=/path/to/model
python scripts/evaluate.py -m model=mock,hf_local data=eval_200
```

This is useful because model choice should remain flexible. The model should be an experimental variable, not a code edit.

## Expected next-week progress

For the next check-in, the repository should demonstrate:

- end-to-end execution on the seed 200-item evaluation set,
- a clear error taxonomy,
- initial baseline metrics,
- a plan for manual auditing of the test set,
- open questions about taxonomy boundaries and expected evaluation standards.
