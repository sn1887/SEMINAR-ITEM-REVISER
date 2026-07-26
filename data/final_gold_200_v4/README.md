# final_gold_200_unique_v4_professor_review Bundle

This bundle contains the 200-item questionnaire-quality benchmark after applying the professor’s review.

## Start here

- `final_gold_200_professor_feedback_changes_v4.md` — readable item-by-item resolution.
- `final_gold_200_unique_v4_professor_review.pretty.json` — easiest full dataset file to inspect.
- `final_gold_200_unique_v4_professor_review.csv` — flat analysis format; multiple labels in `known_errors` are pipe-separated.
- `final_gold_200_unique_v4_professor_review.jsonl` — benchmark/inference format.
- `final_gold_200_validation_v4_professor_review.json` — machine-readable validation results.
- `final_gold_200_summary_v4_professor_review.md` — composition and label counts.

## Important methodological change

The previous exact balance of 12 appearances per label is intentionally not retained. The professor identified additional independently valid flaws, so v4 prioritizes annotation validity over equal label exposure.

## Review scope

21 rows changed:
- 6 clean-control wording/response repairs
- 14 rows with additional labels or revised expected answers
- 1 strengthened `open_closed_mismatch` example

All 200 rows remain present, and all 40 clean controls have identical expected revisions.
