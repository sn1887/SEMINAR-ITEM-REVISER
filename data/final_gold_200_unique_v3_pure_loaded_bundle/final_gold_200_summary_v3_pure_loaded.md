# final_gold_200_unique_v3_pure_loaded Summary

This is a focused v3 cleanup of the 200-item questionnaire-quality benchmark. It keeps the v2 structure but fixes the loaded-question taxonomy issue identified during review.

## What changed from v2

- Rewrote the 8 single-label `loaded_question` rows so the flaw is presuppositional, accusatory, or judgmental stem wording rather than missing `No`, `Never`, or `0` response options.
- Patched the 4 multi-label rows that include `loaded_question` so their intended loaded premise is no longer caused by missing no-event response paths.
- Preserved the 200-row size, 40 clean controls, 160 flawed rows, 128 single-label flawed rows, 32 multi-label flawed rows, and exact 12-appearance balance for every label.

## Final composition

| Category | Count |
|---|---:|
| Total rows | 200 |
| Clean controls | 40 |
| Flawed rows | 160 |
| Single-label flawed rows | 128 |
| Multi-label flawed rows | 32 |

## Label counts

| Label | Total | Single-label | Multi-label appearances |
|---|---:|---:|---:|
| `leading_question` | 12 | 8 | 4 |
| `loaded_question` | 12 | 8 | 4 |
| `double_barreled` | 12 | 8 | 4 |
| `recall_error` | 12 | 8 | 4 |
| `vague_ambiguous` | 12 | 8 | 4 |
| `sensitive_topic_direct` | 12 | 8 | 4 |
| `social_desirability` | 12 | 8 | 4 |
| `negative_wording` | 12 | 8 | 4 |
| `open_closed_mismatch` | 12 | 8 | 4 |
| `agree_disagree_scale` | 12 | 8 | 4 |
| `unbalanced_scale` | 12 | 8 | 4 |
| `incomplete_options` | 12 | 8 | 4 |
| `non_exclusive_options` | 12 | 8 | 4 |
| `missing_scale_labels` | 12 | 8 | 4 |
| `too_many_scale_points` | 12 | 8 | 4 |
| `polarity_mismatch` | 12 | 8 | 4 |


## Loaded-question cleanup audit

| Check | Result |
|---|---:|
| Loaded-question rows total | 12 |
| Loaded-question rows patched in v3 | 12 |
| Single-label loaded-question rows | 8 |
| Multi-label loaded-question rows | 4 |
| Single-label frequency-without-zero flags | 0 |
| Single-label missing-completion flags | 0 |
| Single-label sensitive-context flags | 0 |
| Taxonomy purity passed | True |

## Validation summary

| Check | Result |
|---|---:|
| Exact duplicate questions | 0 |
| Max repeated 5-word opening stem | 3 |
| Max repeated option set | 23 |
| Clean expected revisions identical | 40 / 40 |
| Pairwise similarity >= 0.72 | 0 pairs |
| Maximum pairwise normalized similarity | 0.7083 |
| Core checks passed | True |

## Difficulty distribution

| Difficulty | Count |
|---|---:|
| `obvious` | 67 |
| `realistic` | 67 |
| `borderline` | 66 |

## Topic distribution

| Topic | Count |
|---|---:|
| `politics/public policy` | 13 |
| `education` | 19 |
| `mobility` | 13 |
| `health` | 19 |
| `finances` | 12 |
| `technology` | 15 |
| `environment` | 15 |
| `work` | 13 |
| `public services` | 19 |
| `university life` | 16 |
| `labor` | 10 |
| `family/household` | 16 |
| `media/culture` | 13 |
| `sensitive behaviors` | 7 |

## Response-format distribution

| Item format | Count |
|---|---:|
| `support_oppose` | 15 |
| `binary_yes_no` | 29 |
| `frequency` | 29 |
| `ordinal_categories` | 47 |
| `categorical_closed_ended` | 16 |
| `numeric_ranges` | 35 |
| `open_ended` | 16 |
| `likert_agreement` | 11 |
| `filter_question` | 2 |

## Remaining limitation

This remains an assistant-curated gold-candidate benchmark derived from a synthetic seed pool. It is structurally validated and has undergone a targeted taxonomy cleanup, but a final human/professor signoff is still recommended before calling it externally validated.
