# final_gold_1000 Summary

Source dataset: `data/processed/candidate_v1_2000.jsonl`

## Target composition

- Total rows: 1000
- Clean controls: 200
- Flawed rows: 800
- Single-label flawed rows: 640
- Multi-label flawed rows: 160

## Label counts

| Label | Count |
|---|---:|
| `leading_question` | 60 |
| `loaded_question` | 60 |
| `double_barreled` | 60 |
| `recall_error` | 60 |
| `vague_ambiguous` | 60 |
| `sensitive_topic_direct` | 60 |
| `social_desirability` | 60 |
| `negative_wording` | 60 |
| `open_closed_mismatch` | 60 |
| `agree_disagree_scale` | 60 |
| `unbalanced_scale` | 60 |
| `incomplete_options` | 60 |
| `non_exclusive_options` | 60 |
| `missing_scale_labels` | 60 |
| `too_many_scale_points` | 60 |
| `polarity_mismatch` | 60 |

## Difficulty distribution

| Difficulty | Count |
|---|---:|
| `borderline` | 332 |
| `obvious` | 334 |
| `realistic` | 334 |

## Topic distribution

| Topic | Count |
|---|---:|
| `health` | 130 |
| `public services` | 83 |
| `mobility` | 82 |
| `education` | 81 |
| `labor` | 78 |
| `technology` | 78 |
| `family/household` | 69 |
| `finances` | 69 |
| `media/culture` | 65 |
| `work` | 61 |
| `university life` | 60 |
| `sensitive behaviors` | 49 |
| `politics/public policy` | 48 |
| `environment` | 47 |

## Response-format distribution

| Item format | Count |
|---|---:|
| `ordinal_categories` | 162 |
| `frequency` | 132 |
| `likert_agreement` | 122 |
| `numeric_ranges` | 122 |
| `binary_yes_no` | 113 |
| `categorical_closed_ended` | 112 |
| `support_oppose` | 83 |
| `filter_question` | 82 |
| `open_ended` | 72 |

## Selection logic
- Clean controls: selected as the first 200 candidate non-flawed rows to reduce repetition from disambiguated variants while preserving topic and format diversity.
- Single-label rows: first 40 rows per label, preserving balanced difficulty cycle and minimizing later template repetition.
- Multi-label rows: first 10 rows from each of 16 designed pairs, giving 20 appearances per label in multi-label rows.
- No rows were rewritten; all expected revisions were preserved from candidate source.

## Selection examples
- Accepted clean: `candidate-v1-clean-0001`, `candidate-v1-clean-0002`, `candidate-v1-clean-0003`
- Accepted single: `candidate-v1-single-leading-question-001`, `candidate-v1-single-loaded-question-001`, `candidate-v1-single-double-barreled-001`
- Accepted multi: `candidate-v1-multi-leading-question-unbalanced-scale-001`, `candidate-v1-multi-unbalanced-scale-missing-scale-labels-001`, `candidate-v1-multi-social-desirability-vague-ambiguous-001`
## Rejection-by-quota examples

### Single-label

- `leading_question` skipped first: `candidate-v1-single-leading-question-041`, `candidate-v1-single-leading-question-042`, `candidate-v1-single-leading-question-043`, `candidate-v1-single-leading-question-044`
- `loaded_question` skipped first: `candidate-v1-single-loaded-question-041`, `candidate-v1-single-loaded-question-042`, `candidate-v1-single-loaded-question-043`, `candidate-v1-single-loaded-question-044`
- `double_barreled` skipped first: `candidate-v1-single-double-barreled-041`, `candidate-v1-single-double-barreled-042`, `candidate-v1-single-double-barreled-043`, `candidate-v1-single-double-barreled-044`
- `recall_error` skipped first: `candidate-v1-single-recall-error-041`, `candidate-v1-single-recall-error-042`, `candidate-v1-single-recall-error-043`, `candidate-v1-single-recall-error-044`
- `vague_ambiguous` skipped first: `candidate-v1-single-vague-ambiguous-041`, `candidate-v1-single-vague-ambiguous-042`, `candidate-v1-single-vague-ambiguous-043`, `candidate-v1-single-vague-ambiguous-044`
- `sensitive_topic_direct` skipped first: `candidate-v1-single-sensitive-topic-direct-041`, `candidate-v1-single-sensitive-topic-direct-042`, `candidate-v1-single-sensitive-topic-direct-043`, `candidate-v1-single-sensitive-topic-direct-044`
- `social_desirability` skipped first: `candidate-v1-single-social-desirability-041`, `candidate-v1-single-social-desirability-042`, `candidate-v1-single-social-desirability-043`, `candidate-v1-single-social-desirability-044`
- `negative_wording` skipped first: `candidate-v1-single-negative-wording-041`, `candidate-v1-single-negative-wording-042`, `candidate-v1-single-negative-wording-043`, `candidate-v1-single-negative-wording-044`
- `open_closed_mismatch` skipped first: `candidate-v1-single-open-closed-mismatch-041`, `candidate-v1-single-open-closed-mismatch-042`, `candidate-v1-single-open-closed-mismatch-043`, `candidate-v1-single-open-closed-mismatch-044`
- `agree_disagree_scale` skipped first: `candidate-v1-single-agree-disagree-scale-041`, `candidate-v1-single-agree-disagree-scale-042`, `candidate-v1-single-agree-disagree-scale-043`, `candidate-v1-single-agree-disagree-scale-044`
- `unbalanced_scale` skipped first: `candidate-v1-single-unbalanced-scale-041`, `candidate-v1-single-unbalanced-scale-042`, `candidate-v1-single-unbalanced-scale-043`, `candidate-v1-single-unbalanced-scale-044`
- `incomplete_options` skipped first: `candidate-v1-single-incomplete-options-041`, `candidate-v1-single-incomplete-options-042`, `candidate-v1-single-incomplete-options-043`, `candidate-v1-single-incomplete-options-044`
- `non_exclusive_options` skipped first: `candidate-v1-single-non-exclusive-options-041`, `candidate-v1-single-non-exclusive-options-042`, `candidate-v1-single-non-exclusive-options-043`, `candidate-v1-single-non-exclusive-options-044`
- `missing_scale_labels` skipped first: `candidate-v1-single-missing-scale-labels-041`, `candidate-v1-single-missing-scale-labels-042`, `candidate-v1-single-missing-scale-labels-043`, `candidate-v1-single-missing-scale-labels-044`
- `too_many_scale_points` skipped first: `candidate-v1-single-too-many-scale-points-041`, `candidate-v1-single-too-many-scale-points-042`, `candidate-v1-single-too-many-scale-points-043`, `candidate-v1-single-too-many-scale-points-044`
- `polarity_mismatch` skipped first: `candidate-v1-single-polarity-mismatch-041`, `candidate-v1-single-polarity-mismatch-042`, `candidate-v1-single-polarity-mismatch-043`, `candidate-v1-single-polarity-mismatch-044`

### Multi-label

- `agree_disagree_scale+negative_wording` skipped first: `candidate-v1-multi-agree-disagree-scale-negative-wording-011`, `candidate-v1-multi-agree-disagree-scale-negative-wording-012`, `candidate-v1-multi-agree-disagree-scale-negative-wording-013`, `candidate-v1-multi-agree-disagree-scale-negative-wording-014`
- `double_barreled+leading_question` skipped first: `candidate-v1-multi-double-barreled-leading-question-011`, `candidate-v1-multi-double-barreled-leading-question-012`, `candidate-v1-multi-double-barreled-leading-question-013`, `candidate-v1-multi-double-barreled-leading-question-014`
- `incomplete_options+non_exclusive_options` skipped first: `candidate-v1-multi-incomplete-options-non-exclusive-options-011`, `candidate-v1-multi-incomplete-options-non-exclusive-options-012`, `candidate-v1-multi-incomplete-options-non-exclusive-options-013`, `candidate-v1-multi-incomplete-options-non-exclusive-options-014`
- `leading_question+unbalanced_scale` skipped first: `candidate-v1-multi-leading-question-unbalanced-scale-011`, `candidate-v1-multi-leading-question-unbalanced-scale-012`, `candidate-v1-multi-leading-question-unbalanced-scale-013`, `candidate-v1-multi-leading-question-unbalanced-scale-014`
- `loaded_question+sensitive_topic_direct` skipped first: `candidate-v1-multi-loaded-question-sensitive-topic-direct-011`, `candidate-v1-multi-loaded-question-sensitive-topic-direct-012`, `candidate-v1-multi-loaded-question-sensitive-topic-direct-013`, `candidate-v1-multi-loaded-question-sensitive-topic-direct-014`
- `missing_scale_labels+too_many_scale_points` skipped first: `candidate-v1-multi-missing-scale-labels-too-many-scale-points-011`, `candidate-v1-multi-missing-scale-labels-too-many-scale-points-012`, `candidate-v1-multi-missing-scale-labels-too-many-scale-points-013`, `candidate-v1-multi-missing-scale-labels-too-many-scale-points-014`
- `negative_wording+polarity_mismatch` skipped first: `candidate-v1-multi-negative-wording-polarity-mismatch-011`, `candidate-v1-multi-negative-wording-polarity-mismatch-012`, `candidate-v1-multi-negative-wording-polarity-mismatch-013`, `candidate-v1-multi-negative-wording-polarity-mismatch-014`
- `non_exclusive_options+open_closed_mismatch` skipped first: `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-011`, `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-012`, `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-013`, `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-014`
- `open_closed_mismatch+loaded_question` skipped first: `candidate-v1-multi-open-closed-mismatch-loaded-question-011`, `candidate-v1-multi-open-closed-mismatch-loaded-question-012`, `candidate-v1-multi-open-closed-mismatch-loaded-question-013`, `candidate-v1-multi-open-closed-mismatch-loaded-question-014`
- `polarity_mismatch+incomplete_options` skipped first: `candidate-v1-multi-polarity-mismatch-incomplete-options-011`, `candidate-v1-multi-polarity-mismatch-incomplete-options-012`, `candidate-v1-multi-polarity-mismatch-incomplete-options-013`, `candidate-v1-multi-polarity-mismatch-incomplete-options-014`
- `recall_error+double_barreled` skipped first: `candidate-v1-multi-recall-error-double-barreled-011`, `candidate-v1-multi-recall-error-double-barreled-012`, `candidate-v1-multi-recall-error-double-barreled-013`, `candidate-v1-multi-recall-error-double-barreled-014`
- `sensitive_topic_direct+social_desirability` skipped first: `candidate-v1-multi-sensitive-topic-direct-social-desirability-011`, `candidate-v1-multi-sensitive-topic-direct-social-desirability-012`, `candidate-v1-multi-sensitive-topic-direct-social-desirability-013`, `candidate-v1-multi-sensitive-topic-direct-social-desirability-014`
- `social_desirability+vague_ambiguous` skipped first: `candidate-v1-multi-social-desirability-vague-ambiguous-011`, `candidate-v1-multi-social-desirability-vague-ambiguous-012`, `candidate-v1-multi-social-desirability-vague-ambiguous-013`, `candidate-v1-multi-social-desirability-vague-ambiguous-014`
- `too_many_scale_points+agree_disagree_scale` skipped first: `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-011`, `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-012`, `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-013`, `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-014`
- `unbalanced_scale+missing_scale_labels` skipped first: `candidate-v1-multi-unbalanced-scale-missing-scale-labels-011`, `candidate-v1-multi-unbalanced-scale-missing-scale-labels-012`, `candidate-v1-multi-unbalanced-scale-missing-scale-labels-013`, `candidate-v1-multi-unbalanced-scale-missing-scale-labels-014`
- `vague_ambiguous+recall_error` skipped first: `candidate-v1-multi-vague-ambiguous-recall-error-011`, `candidate-v1-multi-vague-ambiguous-recall-error-012`, `candidate-v1-multi-vague-ambiguous-recall-error-013`, `candidate-v1-multi-vague-ambiguous-recall-error-014`

## Limitations
- Source is synthetic and template-derived, so some wording regularities remain despite balancing.
- Candidate metadata indicates all rows still require manual validation quality signoff; this set is a curated benchmark candidate, not an externally validated field dataset.
- Sensitive wording and social-desirability constructions should receive one additional human audit pass before deployment.
