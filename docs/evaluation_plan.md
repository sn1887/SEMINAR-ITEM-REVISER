# Evaluation Plan for the Item Reviser Agent

## Goal

Evaluate whether an item-reviser agent can identify survey-item problems and produce improved items without introducing new issues.

## Dataset

The final seminar matrix uses the immutable 200-item v4 benchmark at
`data/final_gold_200_v4/final_gold_200_unique_v4.jsonl`, selected with
`data=final_gold_200_v4`. Do not modify this canonical input. The older v3
bundle remains available only for historical comparison.

The older seed dataset contains 200 JSONL records.

Each record has:

```json
{
  "id": "bad-leading-001",
  "question": "...",
  "response_options": ["..."],
  "target_concept": "...",
  "known_errors": ["leading_question"],
  "is_flawed": true,
  "expected_revision": {
    "question": "...",
    "response_options": ["..."]
  }
}
```

## Category families

### Wording errors

- `leading_question`
- `loaded_question`
- `double_barreled`
- `recall_error`
- `vague_ambiguous`
- `sensitive_topic_direct`
- `social_desirability`
- `negative_wording`

### Scale and response-option errors

- `agree_disagree_scale`
- `unbalanced_scale`
- `incomplete_options`
- `non_exclusive_options`
- `missing_scale_labels`
- `too_many_scale_points`
- `polarity_mismatch`

### Structure errors

- `open_closed_mismatch`

## Evaluation modes

- `end_to_end`: detect issues and revise from predicted labels. This preserves
  the current default behavior.
- `detection_only`: run only the detector/checker/router equivalent, leave items
  unchanged, and report detection metrics plus clean false positives. Semantic
  revision metrics and overcorrection are not applicable because no reviser runs.
- `oracle_revision`: use gold labels from the dataset as detected issues, then
  run the reviser to evaluate revision quality independent of detection.
  Detection metrics are oracle-supplied audit values, not model-detection
  performance. Semantic revision metrics are scoped to gold-flawed items with
  valid expected revisions only;
  clean controls are excluded because no revision is attempted for them.

## Primary automatic detection metrics

For error detection:

- micro precision
- micro recall
- micro F1
- exact error-set match
- per-category counts

For end-to-end clean-control behavior:

- false positive rate on clean items
- percentage of clean items that the system revises

Metric applicability is mode-specific and is recorded in `metrics.json` under
`metric_applicability`.

## Supporting semantic revision metrics

Semantic revision scores are computed only once after a completed revision run,
using one cached CPU BERTScore scorer; progress logging does not rescore earlier
rows. They are supporting measures in `end_to_end` mode and primary revision
measures in `oracle_revision` mode. Clean controls are excluded from these
aggregates and remain part of clean false-positive and overcorrection reporting.

- **Question BERTScore F1** (0–1): official `bert-score==0.3.13`, comparing the
  generated question with the gold revised question.
- **SARI** (0–100): Evaluate's maintained `sari` implementation from
  `evaluate==0.4.6`, using original question → generated question against the
  gold revised question. Its module requires `sacremoses==0.1.1` and
  `sacrebleu==2.5.1`. EASSE was not available from the configured package
  index, so this maintained implementation was selected and checked against a
  canonical SARI example.
No semantic response-option score is reported. The investigated option-matching
heuristics were not sufficiently validated across arbitrary survey scales and
could produce misleading similarity values. Exact option match is retained as a
strict, transparent diagnostic, but it can under-credit valid alternative option
wording or ordering and must not be interpreted as general option quality.

Every semantic question metric reports eligible, scored, and failed item counts,
coverage, failure rate, the BERTScore hash, and Torch/Transformers/metric-library
versions. Exact question/option/complete-revision matches and changed rate remain
clearly labelled diagnostics, not semantic quality scores. All are
single-reference automatic measures, so valid alternative repairs can be
penalized.

### Severity Interpretation

Severity is an item-specific impact judgment for each detected issue.

- `low`: minor risk; item is mostly answerable.
- `medium`: likely affects interpretation or response quality.
- `high`: likely invalidates measurement or makes responses misleading.

Do not treat severity as model confidence or benchmark difficulty. For
multi-label items, assign severity per issue; when an item-level summary is
needed, use the highest issue severity. A high-severity issue should be
considered unresolved unless the revision directly restores valid measurement.

## Commands

```bash
python scripts/evaluate.py \
  experiment=item_reviser_eval \
  data=final_gold_200_v4 \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL
```

```bash
python scripts/evaluate.py data=final_gold_200_v4 prompt=baseline_p1 evaluator.mode=end_to_end
python scripts/evaluate.py data=final_gold_200_v4 prompt=orchestration_p2 orchestration.enabled=true evaluator.mode=oracle_revision
```
