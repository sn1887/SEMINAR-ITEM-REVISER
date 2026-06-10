from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from item_reviser.evaluation.dataset import load_eval_dataset_with_metadata  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="data/eval/test_set_200_seed.jsonl")
    args = parser.parse_args()
    items, metadata = load_eval_dataset_with_metadata(args.path)
    id_counter = Counter(item.id for item in items)
    duplicate_ids = [item_id for item_id, count in id_counter.items() if count > 1]
    categories = Counter(category for item in items for category in item.known_errors)
    clean = sum(1 for item in items if not item.known_errors)
    print(f"Dataset path: {metadata.path}")
    print(f"Dataset schema version: {metadata.schema_version}")
    print(f"Dataset hash: {metadata.hash}")
    print(f"Items: {len(items)}")
    print(f"Returned records (after max_items): {metadata.returned_records}")
    print(f"Clean controls: {clean}")
    print(f"Duplicate IDs: {duplicate_ids}")
    if metadata.unknown_categories:
        print(f"Unknown categories: {metadata.unknown_categories}")
    print("Category counts:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    if metadata.missing_required_fields:
        print(f"Missing required fields: {metadata.missing_required_fields}")
    if metadata.malformed_rows:
        print(f"Malformed rows: {metadata.malformed_rows}")


if __name__ == "__main__":
    main()
