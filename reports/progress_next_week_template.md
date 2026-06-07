# Progress Update: Item Reviser Agent

## Current status

- Repository created with Hydra configs.
- 200-item seed evaluation set created.
- Rule-based baseline implemented for wording and scale checks.
- Evaluation pipeline writes predictions, metrics, and report.

## Completed tasks

- [ ] Local install works.
- [ ] `python scripts/evaluate.py model=mock` runs.
- [ ] `metrics.json` generated.
- [ ] 200-item test set reviewed at least once.

## Issues/blockers

- Need first LRZ model benchmark.
- Need feedback on taxonomy and gold labels.

## Evaluation set

- Total items: 200.
- Includes flawed and clean controls.
- Includes wording and scale problems.
- Still needs manual audit before final gold version.

## Questions for Bolei and Caro

1. Are the current categories too broad or too detailed?
2. Should the final evaluation score each error independently?
3. Should the agent revise items with multiple errors in one step or one step per error?
4. Which local model should I benchmark first?
