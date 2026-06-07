from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from item_reviser.schemas import PipelineResult, SurveyItem


def compute_detection_metrics(items: list[SurveyItem], results: list[PipelineResult]) -> dict[str, Any]:
    if len(items) != len(results):
        raise ValueError("items and results must have same length")

    tp = fp = fn = 0
    exact = 0
    clean_total = 0
    clean_false_positive = 0
    clean_changed = 0
    by_category: dict[str, Counter[str]] = defaultdict(Counter)

    for item, result in zip(items, results, strict=True):
        gold = set(item.known_errors)
        pred = set(result.predicted_categories())
        if gold == pred:
            exact += 1
        for c in pred & gold:
            tp += 1
            by_category[c]["tp"] += 1
        for c in pred - gold:
            fp += 1
            by_category[c]["fp"] += 1
        for c in gold - pred:
            fn += 1
            by_category[c]["fn"] += 1

        if not gold:
            clean_total += 1
            if pred:
                clean_false_positive += 1
            if result.revised_item.changed:
                clean_changed += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    exact_match = exact / len(items) if items else 0.0
    false_positive_rate_clean = clean_false_positive / clean_total if clean_total else 0.0
    overcorrection_rate = clean_changed / clean_total if clean_total else 0.0

    return {
        "num_items": len(items),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match": exact_match,
        "clean_items": clean_total,
        "false_positive_rate_on_clean_items": false_positive_rate_clean,
        "overcorrection_rate": overcorrection_rate,
        "by_category": {cat: dict(counts) for cat, counts in sorted(by_category.items())},
    }
