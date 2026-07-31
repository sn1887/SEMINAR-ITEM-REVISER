from __future__ import annotations

from pathlib import Path
from typing import Any


def _format_metric(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "n/a"
    return f"{value:.3f}"


def _evaluation_mode(metrics: dict[str, Any]) -> str:
    return str(
        metrics.get("evaluation_mode")
        or metrics.get("evaluator", {}).get("mode")
        or "end_to_end"
    )


def _detection_section(metrics: dict[str, Any]) -> list[str]:
    applicability = metrics.get("metric_applicability", {}).get("detection", {})
    status = applicability.get("status", "applicable")
    if status == "oracle_supplied":
        return [
            "## Detection Metrics",
            "",
            (
                "Not applicable as model-detection performance: gold labels were "
                "supplied as detected issues in oracle_revision mode."
            ),
            (
                "Oracle-supplied label agreement is retained in metrics.json under "
                "`oracle_supplied_detection_metrics` for audit only."
            ),
            "",
        ]

    lines = [
        "## Primary Detection Metrics",
        "",
        f"- Precision (micro error-label): {_format_metric(metrics.get('precision'))}",
        f"- Recall (micro error-label): {_format_metric(metrics.get('recall'))}",
        f"- F1 (micro error-label): {_format_metric(metrics.get('f1'))}",
        f"- Exact label-set match: {_format_metric(metrics.get('exact_match'))}",
        (
            "- Clean false-positive rate: "
            f"{_format_metric(metrics.get('false_positive_rate_on_clean_items'))}"
        ),
    ]
    overcorrection = metrics.get("metric_applicability", {}).get("overcorrection", {})
    if overcorrection.get("status", "applicable") == "applicable":
        lines.append(
            "- Overcorrection rate on clean items: "
            f"{_format_metric(metrics.get('overcorrection_rate'))}"
        )
    else:
        lines.append("- Overcorrection rate on clean items: n/a")
        lines.append(f"  Reason: {overcorrection.get('reason', 'Not applicable.')}")
    lines.extend(
        [
            "",
            f"- Manual-review flagged items: {metrics.get('manual_review', {}).get('items_flagged_for_review', 0)}",
            f"- Manual-review change rate: {_format_metric(metrics.get('manual_review', {}).get('items_flagged_change_rate'))}",
            "",
        ]
    )
    return lines


def _revision_section(metrics: dict[str, Any]) -> list[str]:
    revision_quality = metrics.get("revision_quality", {})
    applicability = metrics.get("metric_applicability", {}).get("revision_semantic", {})
    if not revision_quality:
        return []
    if applicability.get("status") == "not_applicable":
        return [
            "## Semantic Revision Metrics",
            "",
            f"Not applicable: {applicability.get('reason', 'The reviser was not run.')}",
            "",
        ]
    if applicability.get("status") == "pending":
        return [
            "## Semantic Revision Metrics",
            "",
            f"Pending: {applicability.get('reason', 'Awaiting final scoring.')}",
            "",
        ]

    bertscore = revision_quality.get("question_bertscore_f1", {})
    sari = revision_quality.get("sari", {})
    coverage = (
        f"scored {revision_quality.get('scored_items', 0)}/"
        f"{revision_quality.get('eligible_items', 0)}; "
        f"coverage {_format_metric(revision_quality.get('coverage'))}; "
        f"failed {revision_quality.get('failed_items', 0)} "
        f"({_format_metric(revision_quality.get('failure_rate'))})"
    )

    return [
        "## Semantic Revision Metrics",
        "",
        (
            "These supporting measures compare generated revisions with one gold "
            "reference on gold-flawed items only; clean controls are excluded."
        ),
        (
            "A valid alternative revision can still be penalized by a single-reference "
            "automatic metric."
        ),
        "",
        f"- Scope: {revision_quality.get('scope', 'gold-flawed valid revisions')}",
        f"- Aggregate coverage: {coverage}",
        f"- Question BERTScore F1 (0–1): {_format_metric(bertscore.get('value'))}",
        f"  ({bertscore.get('scored_items', 0)}/{bertscore.get('eligible_items', 0)} scored)",
        f"- Question SARI (0–100): {_format_metric(sari.get('value'))}",
        f"  ({sari.get('scored_items', 0)}/{sari.get('eligible_items', 0)} scored)",
        "",
        "Exact-match and change-rate diagnostics (not semantic quality scores):",
        f"- Exact question match rate: {_format_metric(revision_quality.get('exact_question_match_rate'))}",
        f"- Exact option match rate: {_format_metric(revision_quality.get('exact_option_match_rate'))}",
        "  This is a strict diagnostic and can under-credit valid alternative option wording.",
        f"- Exact revision match rate: {_format_metric(revision_quality.get('exact_revision_rate'))}",
        f"- Revision changed rate: {_format_metric(revision_quality.get('revision_changed_rate'))}",
        "",
    ]


def write_markdown_report(path: str | Path, metrics: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    evaluation_mode = _evaluation_mode(metrics)
    lines = [
        "# Item Reviser Evaluation Report",
        "",
        "## Run Summary",
        "",
        f"- Items: {metrics.get('num_items')}",
        f"- Successful items: {metrics.get('successful_items', metrics.get('num_items', 0))}",
        f"- Failed items: {metrics.get('failed_items', 0)}",
        f"- Failure rate: {_format_metric(metrics.get('failure_rate'))}",
        f"- Evaluation mode: {evaluation_mode}",
        "",
    ]

    if evaluation_mode == "oracle_revision":
        lines.extend(_revision_section(metrics))
        lines.extend(_detection_section(metrics))
    else:
        lines.extend(_detection_section(metrics))
        lines.extend(_revision_section(metrics))

    lines.extend(
        [
            "## By-category counts",
            "",
            "| Category | TP | FP | FN |",
            "|---|---:|---:|---:|",
        ]
    )
    for cat, counts in metrics.get("by_category", {}).items():
        lines.append(f"| {cat} | {counts.get('tp', 0)} | {counts.get('fp', 0)} | {counts.get('fn', 0)} |")

    failures = metrics.get("failures", {})
    if failures and failures.get("count", 0):
        lines.extend(
            [
                "",
                "## Evaluation failures",
                "",
                "| Error type | Count |",
                "|---|---:|",
            ]
        )
        for error_type, count in failures.get("types", {}).items():
            lines.append(f"| {error_type} | {count} |")

    severity = metrics.get("severity_weighted", {})
    if severity.get("enabled"):
        lines.extend(
            [
                "",
                "## Severity-weighted metrics",
                "",
                f"- Precision: {_format_metric(severity.get('precision'))}",
                f"- Recall: {_format_metric(severity.get('recall'))}",
                f"- F1: {_format_metric(severity.get('f1'))}",
            ]
        )

    artifacts = metrics.get("artifacts", {})
    if artifacts:
        lines.extend(
            [
                "",
                "## Artifact mode",
                "",
                f"- Prediction IDs: {artifacts.get('prediction_id_mode', 'unknown')}",
                f"- Gold/source fields in prediction rows: {artifacts.get('gold_in_prediction_rows', False)}",
                f"- Manual-review rows: {artifacts.get('manual_review_rows', 0)}",
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
            "Metric applicability depends on evaluator.mode and is recorded in metrics.json.",
            "Revision-similarity metrics are automatic proxies and do not replace manual evaluation.",
        ]
    )
    severity_metadata = metrics.get("severity", {})
    if severity_metadata.get("orchestration_router_output") == "not_predicted":
        lines.append(
            "For orchestration runs, the router does not predict severity; any routed "
            "issue severity value is synthetic compatibility metadata."
        )
    path.write_text("\n".join(lines), encoding="utf-8")
