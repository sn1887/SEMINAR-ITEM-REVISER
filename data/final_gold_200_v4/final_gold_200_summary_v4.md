# final_gold_200_unique_v4_professor_review Summary

This v4 bundle applies the professor’s item-level review to the v3 benchmark. It retains all 200 rows and the 40/160 clean–flawed split, repairs six clean controls, strengthens one ambiguous `open_closed_mismatch` example, and adds independently valid labels to fourteen flawed rows.

## Main changes

- Items003, 013, and 040 now use count categories consistently rather than mixing counts with rates.
- Items007, 008, and 027 now ask for explicit rates or proportions instead of vague verbal frequency judgments.
- Items090–093 add `vague_ambiguous`.
- Item100 adds `agree_disagree_scale`.
- Item110 now contains an unmistakable open/closed mismatch.
- Items153–160 add `missing_scale_labels`.
- Item191 adds `negative_wording` and receives a neutral categorical revision.

## Composition

| Category | Count |
|---|---:|
| Total rows | 200 |
| Clean controls | 40 |
| Flawed rows | 160 |
| Single-label flawed rows | 115 |
| Multi-label flawed rows | 45 |
| Total label appearances | 206 |
| Rows changed in v4 | 21 |

## Label counts

| Label | Total | Single-label | Multi-label appearances |
|---|---:|---:|---:|
| `leading_question` | 12 | 8 | 4 |
| `loaded_question` | 12 | 8 | 4 |
| `double_barreled` | 12 | 8 | 4 |
| `recall_error` | 12 | 8 | 4 |
| `vague_ambiguous` | 16 | 8 | 8 |
| `sensitive_topic_direct` | 12 | 8 | 4 |
| `social_desirability` | 12 | 4 | 8 |
| `negative_wording` | 13 | 7 | 6 |
| `open_closed_mismatch` | 12 | 8 | 4 |
| `agree_disagree_scale` | 13 | 8 | 5 |
| `unbalanced_scale` | 12 | 8 | 4 |
| `incomplete_options` | 12 | 8 | 4 |
| `non_exclusive_options` | 12 | 8 | 4 |
| `missing_scale_labels` | 20 | 8 | 12 |
| `too_many_scale_points` | 12 | 0 | 12 |
| `polarity_mismatch` | 12 | 8 | 4 |

## Balance decision

The old exact “12 appearances per label” constraint is **not preserved**. The review showed that several items genuinely instantiate more than one flaw. This version prioritizes annotation fidelity over an artificially balanced label distribution. The unchanged labels remain at 12 appearances; `vague_ambiguous`, `agree_disagree_scale`, `missing_scale_labels`, and `negative_wording` increase where the professor identified additional valid defects.

## Validation summary

| Check | Result |
|---|---:|
| Exact duplicate questions | 0 |
| Max repeated 5-word opening stem | 4 |
| Max repeated option set | 23 |
| Clean expected revisions identical | 40 / 40 |
| Pairwise similarity ≥ 0.72 | 0 pairs |
| Maximum pairwise normalized similarity | 0.7083 |
| Professor-feedback checks passed | True |
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
| `education` | 19 |
| `health` | 19 |
| `public services` | 19 |
| `university life` | 16 |
| `family/household` | 16 |
| `technology` | 15 |
| `environment` | 15 |
| `politics/public policy` | 13 |
| `mobility` | 13 |
| `work` | 13 |
| `media/culture` | 13 |
| `finances` | 12 |
| `labor` | 10 |
| `sensitive behaviors` | 7 |

## Response-format distribution

| Item format | Count |
|---|---:|
| `ordinal_categories` | 47 |
| `numeric_ranges` | 35 |
| `binary_yes_no` | 29 |
| `frequency` | 29 |
| `categorical_closed_ended` | 17 |
| `support_oppose` | 15 |
| `open_ended` | 15 |
| `likert_agreement` | 11 |
| `filter_question` | 2 |

## Recommended use

Use this version for benchmark evaluation when natural multilabel annotation is more important than equal label frequency. For model-comparison statistics, report per-label sample sizes because the reviewed labels are no longer balanced.
