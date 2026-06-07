# Evaluation Plan for the Item Reviser Agent

## Goal

Evaluate whether an item-reviser agent can identify survey-item problems and produce improved items without introducing new issues.

## Dataset

The initial seed dataset contains 200 JSONL records.

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

## Automatic metrics

For error detection:

- micro precision
- micro recall
- micro F1
- exact error-set match
- per-category counts

For overcorrection:

- false positive rate on clean items
- percentage of clean items that the system revises

For revision quality, automatic metrics are only weak proxies. The final paper should include manual assessment.

## Manual evaluation rubric

For each model output, rate:

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Error detection | missed/wrong | partly correct | correct |
| Explanation | wrong | vague | accurate |
| Revision fixes problem | no | partly | yes |
| Preserves concept | no | partly | yes |
| Introduces new issue | yes | unclear | no |

## Recommended evaluation protocol

1. Run deterministic baseline.
2. Run at least one local LLM.
3. Compare model outputs on the same 200 items.
4. Manually inspect 30–50 outputs.
5. Report automatic metrics plus qualitative examples.

## Commands

```bash
python scripts/evaluate.py experiment=item_reviser_eval model=mock
```

Later, for a local model:

```bash
python scripts/evaluate.py \
  experiment=item_reviser_eval \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL
```
