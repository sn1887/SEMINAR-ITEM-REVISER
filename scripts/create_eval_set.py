from __future__ import annotations

# The seed dataset is already committed under data/eval/test_set_200_seed.jsonl.
# This script is a placeholder for future regenerated data creation after taxonomy decisions.

from pathlib import Path


def main() -> None:
    path = Path("data/eval/test_set_200_seed.jsonl")
    print(f"Seed dataset exists at {path.resolve()}")
    print("For now, edit/generate data through notebooks or a reviewed script, then validate with scripts/validate_eval_set.py.")


if __name__ == "__main__":
    main()
