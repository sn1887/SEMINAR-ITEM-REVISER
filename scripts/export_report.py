from __future__ import annotations

import argparse
import json
from pathlib import Path

from item_reviser.evaluation.report import write_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics_json")
    parser.add_argument("output_md")
    args = parser.parse_args()
    metrics = json.loads(Path(args.metrics_json).read_text(encoding="utf-8"))
    write_markdown_report(args.output_md, metrics)


if __name__ == "__main__":
    main()
