from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from item_reviser.evaluation.report import write_markdown_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics_json")
    parser.add_argument("output_md")
    args = parser.parse_args()
    metrics = json.loads(Path(args.metrics_json).read_text(encoding="utf-8"))
    write_markdown_report(args.output_md, metrics)


if __name__ == "__main__":
    main()
