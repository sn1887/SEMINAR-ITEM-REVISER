# Progress Report for Next Week

## One-sentence project summary

I am building an Item Reviser Agent that checks survey questions for wording and scale problems and proposes improved items while avoiding overcorrection.

## What is already done

- Created a Hydra-based research repository.
- Added LLM-backed quality-checking and revision agents.
- Added a 200-item seed evaluation set.
- Added evaluation metrics and report generation.
- Kept model backend flexible for later LRZ model benchmarking.

## What I can show

Run:

```bash
python scripts/evaluate.py \
  experiment=item_reviser_eval \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL
```

Then show:

- `predictions.jsonl`,
- `metrics.json`,
- `report.md`.

## Evaluation/test set status

The current 200-item seed set includes:

- flawed items with one or more expected errors,
- clean control items,
- wording errors,
- scale errors,
- sensitive/social desirability examples,
- overcorrection cases.

It still needs manual review before becoming final gold data.

## Questions for Bolei and Caro

1. Should the final evaluation data be fully synthetic, real, or mixed?
2. Should each test item have one primary error label or multiple labels?
3. How should revisions be graded?
4. Which local LRZ model should be benchmarked first?
5. Should decoding be fixed across models or tuned per model family?
