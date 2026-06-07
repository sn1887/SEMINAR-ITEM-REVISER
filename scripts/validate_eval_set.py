from __future__ import annotations

import argparse
from collections import Counter

from item_reviser.io import load_items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="data/eval/test_set_200_seed.jsonl")
    args = parser.parse_args()
    items = load_items(args.path)
    ids = [item.id for item in items]
    duplicate_ids = [item_id for item_id, count in Counter(ids).items() if count > 1]
    categories = Counter(cat for item in items for cat in item.known_errors)
    clean = sum(1 for item in items if not item.known_errors)
    print(f"Items: {len(items)}")
    print(f"Clean controls: {clean}")
    print(f"Duplicate IDs: {duplicate_ids}")
    print("Category counts:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
