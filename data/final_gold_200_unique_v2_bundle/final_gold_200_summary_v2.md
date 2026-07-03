# final_gold_200_unique_v2 Summary

## Construction rationale

The original 1,000-item pool was used as a seed pool for taxonomy, labels, topics, response formats, and traceability. The final 200 were selected and rewritten rather than copied directly. Version 2 additionally synchronizes clean-control expected revisions and reduces the strongest high-similarity wording clusters.

## Target composition achieved

| Type | Count |
|---|---:|
| Total rows | 200 |
| Clean controls | 40 |
| Flawed rows | 160 |
| Single-label flawed rows | 128 |
| Multi-label flawed rows | 32 |

## Label exposure counts

| Label | Total appearances |
|---|---:|
| `leading_question` | 12 |
| `loaded_question` | 12 |
| `double_barreled` | 12 |
| `recall_error` | 12 |
| `vague_ambiguous` | 12 |
| `sensitive_topic_direct` | 12 |
| `social_desirability` | 12 |
| `negative_wording` | 12 |
| `open_closed_mismatch` | 12 |
| `agree_disagree_scale` | 12 |
| `unbalanced_scale` | 12 |
| `incomplete_options` | 12 |
| `non_exclusive_options` | 12 |
| `missing_scale_labels` | 12 |
| `too_many_scale_points` | 12 |
| `polarity_mismatch` | 12 |

Each label has exactly 8 single-label rows plus 4 multi-label appearances, for 12 total appearances.

## Difficulty distribution

| Difficulty | Count |
|---|---:|
| `obvious` | 67 |
| `realistic` | 67 |
| `borderline` | 66 |

## Topic distribution

| Topic | Count |
|---|---:|
| `public services` | 19 |
| `education` | 18 |
| `health` | 18 |
| `family/household` | 16 |
| `environment` | 15 |
| `university life` | 15 |
| `technology` | 14 |
| `media/culture` | 13 |
| `sensitive behaviors` | 13 |
| `work` | 13 |
| `finances` | 12 |
| `mobility` | 12 |
| `politics/public policy` | 12 |
| `labor` | 10 |

## Response-format distribution

| Item format | Count |
|---|---:|
| `ordinal_categories` | 45 |
| `numeric_ranges` | 34 |
| `binary_yes_no` | 28 |
| `frequency` | 28 |
| `categorical_closed_ended` | 15 |
| `open_ended` | 15 |
| `support_oppose` | 14 |
| `likert_agreement` | 11 |
| `filter_question` | 10 |

## Validation summary

- Exact duplicate final questions: 0.
- Clean controls with identical expected revisions: 40/40.
- Maximum repeated 5-word opening stem: 3.
- Maximum repeated response-option set: 23.
- Maximum pairwise normalized string similarity: 0.708.
- Pairwise normalized string similarity >= 0.72: 0 pairs.
- All 16 labels have exactly 12 appearances.

## Limitations

This is an assistant-curated academic benchmark candidate derived from a synthetic seed pool. It passed structural and lexical validation, but independent human/professor signoff is still recommended before formal deployment in a thesis, publication, or grading setup.
