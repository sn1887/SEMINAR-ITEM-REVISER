from __future__ import annotations

from pathlib import Path
from typing import Any


def write_markdown_report(path: str | Path, metrics: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Item Reviser Evaluation Report",
        "",
        "## Summary metrics",
        "",
        f"- Items: {metrics.get('num_items')}",
        f"- Precision: {metrics.get('precision', 0):.3f}",
        f"- Recall: {metrics.get('recall', 0):.3f}",
        f"- F1: {metrics.get('f1', 0):.3f}",
        f"- Exact match: {metrics.get('exact_match', 0):.3f}",
        f"- False positive rate on clean items: {metrics.get('false_positive_rate_on_clean_items', 0):.3f}",
        f"- Overcorrection rate: {metrics.get('overcorrection_rate', 0):.3f}",
        "",
        "## By-category counts",
        "",
        "| Category | TP | FP | FN |",
        "|---|---:|---:|---:|",
    ]
    for cat, counts in metrics.get("by_category", {}).items():
        lines.append(f"| {cat} | {counts.get('tp', 0)} | {counts.get('fp', 0)} | {counts.get('fn', 0)} |")
    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "These automatic metrics evaluate detection of known error categories. They do not fully evaluate whether the revised question is substantively good. Manual evaluation is still required.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
