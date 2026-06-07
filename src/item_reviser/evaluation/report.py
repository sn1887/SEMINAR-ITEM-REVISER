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
        f"- Manual-review flagged items: {metrics.get('manual_review', {}).get('items_flagged_for_review', 0)}",
        f"- Manual-review change rate: {metrics.get('manual_review', {}).get('items_flagged_change_rate', 0):.3f}",
        "",
        "## By-category counts",
        "",
        "| Category | TP | FP | FN |",
        "|---|---:|---:|---:|",
    ]
    for cat, counts in metrics.get("by_category", {}).items():
        lines.append(f"| {cat} | {counts.get('tp', 0)} | {counts.get('fp', 0)} | {counts.get('fn', 0)} |")

    revision_quality = metrics.get("revision_quality", {})
    if revision_quality:
        lines.extend(
            [
                "",
                "## Revision quality",
                "",
                f"- Items with expected revisions: {revision_quality.get('items_with_expected_revision', 0)}",
                f"- Mean question similarity: {revision_quality.get('mean_question_similarity', 0):.3f}",
                f"- Mean response-option Jaccard: {revision_quality.get('mean_option_jaccard', 0):.3f}",
                f"- Exact question match rate: {revision_quality.get('exact_question_match_rate', 0):.3f}",
                f"- Exact option match rate: {revision_quality.get('exact_option_match_rate', 0):.3f}",
                f"- Exact revision match rate: {revision_quality.get('exact_revision_rate', 0):.3f}",
                f"- Revision changed rate: {revision_quality.get('revision_changed_rate', 0):.3f}",
            ]
        )

    severity = metrics.get("severity_weighted", {})
    if severity.get("enabled"):
        lines.extend(
            [
                "",
                "## Severity-weighted metrics",
                "",
                f"- Precision: {severity.get('precision', 0):.3f}",
                f"- Recall: {severity.get('recall', 0):.3f}",
                f"- F1: {severity.get('f1', 0):.3f}",
            ]
        )

    dataset_info = metrics.get("dataset", {})
    if dataset_info:
        lines.extend(
            [
                "",
                "## Dataset metadata",
                "",
                f"- Dataset: {dataset_info.get('path')}",
                f"- Schema version: {dataset_info.get('schema_version', 'n/a')}",
                f"- Hash ({dataset_info.get('hash_algorithm', 'sha256')}): {dataset_info.get('hash', 'n/a')}",
                f"- Returned items: {dataset_info.get('returned_records', dataset_info.get('file_records', 0))}",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "These automatic metrics evaluate detection of known error categories and revision similarity.",
            "They do not fully replace manual evaluation.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
