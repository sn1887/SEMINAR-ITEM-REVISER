# Data Directory

The final submission keeps only the final-facing benchmark data.

- `final_gold_200_v4/final_gold_200_unique_v4.jsonl`: canonical 200-item v4
  benchmark used by the final experiment matrix.
- `final_gold_200_v4/final_gold_200_unique_v4.csv`: spreadsheet view of the
  same benchmark.
- `final_gold_200_v4/final_gold_200_summary_v4.md`: composition, label counts,
  validation summary, difficulty distribution, and topic distribution.
- `examples/demo_items.jsonl`: tiny demonstration file.
- `raw/`: placeholder for local uncommitted source data.
- `processed/`: placeholder for regenerated derived artifacts, ignored by Git
  except for `.gitkeep`.

Hydra defaults to the final v4 benchmark via `configs/data/final_gold_200_v4.yaml`.

Validate the benchmark with:

```bash
python scripts/validate_eval_set.py
```
