# Final Gold 200 v4

This folder contains the final 200-item gold benchmark after applying the
professor review pass. It is intentionally kept small so readers can find the
dataset without sorting through generation logs and audit scratch files.

## Files

- `final_gold_200_unique_v4.jsonl` - canonical benchmark/inference file.
- `final_gold_200_unique_v4.csv` - spreadsheet view of the same 200 rows.
- `final_gold_200_unique_v4_questionnaire_catalog.pdf` - reader-facing PDF
  catalog of all 200 survey items, annotations, and expected revisions.
- `final_gold_200_unique_v4_questionnaire_catalog.tex` - LaTeX source used to
  build the PDF catalog.
- `final_gold_200_summary_v4.md` - composition, label counts, validation
  summary, difficulty distribution, and topic distribution.
- `README.md` - this guide.

## Notes

The dataset keeps all 200 rows and the 40 clean / 160 flawed split. The earlier
exact label balance is intentionally not preserved because the professor review
identified additional independently valid flaws. Version 4 therefore prioritizes
annotation validity over artificial per-label balance.

Generation traces, detailed audit files, source maps, duplicate pretty JSON, and
intermediate review notes were removed from this final-facing folder to avoid
confusing readers.
