# candidate_v1_2000 Summary

Generated `candidate_v1_2000.jsonl` as a literature-grounded candidate benchmark for the item-reviser. The existing seed set at `data/eval/test_set_200_seed.jsonl` was not modified.

## Counts

- Total rows: 2000
- Clean controls: 400
- Flawed rows: 1600
- Single-label flawed rows: 1280
- Multi-label flawed rows: 320
- Dataset SHA-256: `379eec4e2ba38436c7e220af83f14518d448278901a408b859645e5e0fcd0294`
- Seed set SHA-256 after generation: `80d5f15fe87ae8bb9eb00fe79ac990759a230dbee2ffc71e99f4a3ef16be5404`

## Taxonomy Label Counts

Single-label rows contribute 80 examples per label. Multi-label rows contribute 40 additional examples per label, so each taxonomy label appears 120 times in candidate_v1.

| Label | Count |
|---|---:|
| `agree_disagree_scale` | 120 |
| `double_barreled` | 120 |
| `incomplete_options` | 120 |
| `leading_question` | 120 |
| `loaded_question` | 120 |
| `missing_scale_labels` | 120 |
| `negative_wording` | 120 |
| `non_exclusive_options` | 120 |
| `open_closed_mismatch` | 120 |
| `polarity_mismatch` | 120 |
| `recall_error` | 120 |
| `sensitive_topic_direct` | 120 |
| `social_desirability` | 120 |
| `too_many_scale_points` | 120 |
| `unbalanced_scale` | 120 |
| `vague_ambiguous` | 120 |

## Topic Distribution

| Topic | Count |
|---|---:|
| `education` | 151 |
| `environment` | 109 |
| `family/household` | 139 |
| `finances` | 149 |
| `health` | 246 |
| `labor` | 143 |
| `media/culture` | 138 |
| `mobility` | 170 |
| `politics/public policy` | 87 |
| `public services` | 170 |
| `sensitive behaviors` | 97 |
| `technology` | 162 |
| `university life` | 129 |
| `work` | 110 |

## Response-Format Distribution

| Item format | Count |
|---|---:|
| `binary_yes_no` | 225 |
| `categorical_closed_ended` | 224 |
| `filter_question` | 165 |
| `frequency` | 264 |
| `likert_agreement` | 245 |
| `numeric_ranges` | 244 |
| `open_ended` | 144 |
| `ordinal_categories` | 324 |
| `support_oppose` | 165 |

## Difficulty Distribution

| Difficulty | Count |
|---|---:|
| `borderline` | 666 |
| `obvious` | 667 |
| `realistic` | 667 |

## Known Limitations and Review Risks

- This is candidate_v1, not final gold. All rows are marked `needs_manual_review: true`.
- Items are synthetic and template-assisted. They are designed for coverage and auditability, not for claiming population-realistic item frequencies.
- Some labels, especially `too_many_scale_points`, `missing_scale_labels`, and `agree_disagree_scale`, are context-sensitive in the literature. Reviewers should confirm that the intended correction is appropriate for each target concept.
- Clean controls include a few nuanced but acceptable formats, including direct agreement items whose target concept is explicitly agreement. They should be audited for overcorrection risk.
- Multi-label rows use realistic two-label combinations only. This keeps label incidence exactly balanced, but a future v2 could add carefully reviewed three-label cases.
- Expected revisions are minimal benchmark references, not the only acceptable revisions.
