from __future__ import annotations

from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import Any

from item_reviser.constants import CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY
from item_reviser.schemas import PipelineResult, SurveyItem
from item_reviser.utils import normalize_text


def _jaccard_similarity(left: list[str], right: list[str]) -> float:
    left_set = {normalize_text(x) for x in left}
    right_set = {normalize_text(x) for x in right}
    if not left_set and not right_set:
        return 1.0
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _text_similarity(left: str, right: str) -> float:
    left_clean = normalize_text(left)
    right_clean = normalize_text(right)
    if not left_clean and not right_clean:
        return 1.0
    if not left_clean or not right_clean:
        return 0.0
    return SequenceMatcher(None, left_clean, right_clean).ratio()


def _category_weight(category: str, weights: dict[str, float] | None) -> float:
    if weights is None:
        return 0.0
    return float(weights.get(category, 0.5))


def compute_detection_metrics(
    items: list[SurveyItem],
    results: list[PipelineResult],
    *,
    use_severity_weighting: bool = False,
    category_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    if len(items) != len(results):
        raise ValueError("items and results must have same length")

    tp = fp = fn = 0
    exact = 0
    clean_total = 0
    clean_false_positive = 0
    clean_changed = 0
    manual_total = 0
    manual_changed = 0
    manual_clean_changes = 0

    revision_items = 0
    question_similarity_sum = 0.0
    option_similarity_sum = 0.0
    exact_question_matches = 0
    exact_option_matches = 0
    exact_revision_count = 0
    changed_count = 0

    weighted_tp = 0.0
    weighted_fp = 0.0
    weighted_fn = 0.0
    by_category: dict[str, Counter[str]] = defaultdict(Counter)

    severity_weights = CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY if use_severity_weighting else None
    if category_weights is not None:
        severity_weights = dict(category_weights)

    for item, result in zip(items, results, strict=True):
        gold = set(item.known_errors)
        pred = set(result.predicted_categories())

        if gold == pred:
            exact += 1

        for c in pred & gold:
            tp += 1
            weighted_tp += _category_weight(c, severity_weights)
            by_category[c]["tp"] += 1

        for c in pred - gold:
            fp += 1
            weighted_fp += _category_weight(c, severity_weights)
            by_category[c]["fp"] += 1

        for c in gold - pred:
            fn += 1
            weighted_fn += _category_weight(c, severity_weights)
            by_category[c]["fn"] += 1

        if not gold:
            clean_total += 1
            if pred:
                clean_false_positive += 1
            if result.revised_item.changed:
                clean_changed += 1

        if item.needs_manual_review():
            manual_total += 1
            if result.revised_item.changed:
                manual_changed += 1
                if not gold:
                    manual_clean_changes += 1

        expected = item.expected_revision or {}
        expected_q = str(expected.get("question", "")).strip()
        expected_opts = expected.get("response_options") or []
        has_expected = bool(expected_q) or bool(expected_opts)
        if has_expected:
            revision_items += 1
            revised_question = result.revised_item.question
            revised_options = result.revised_item.response_options

            q_similarity = _text_similarity(expected_q, revised_question)
            option_similarity = _jaccard_similarity(
                [str(opt) for opt in expected_opts],
                [str(opt) for opt in revised_options],
            )
            question_similarity_sum += q_similarity
            option_similarity_sum += option_similarity

            if normalize_text(expected_q) == normalize_text(revised_question):
                exact_question_matches += 1
            if option_similarity == 1.0:
                exact_option_matches += 1
            if (
                normalize_text(expected_q) == normalize_text(revised_question)
                and option_similarity == 1.0
            ):
                exact_revision_count += 1
            if result.revised_item.changed:
                changed_count += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    exact_match = exact / len(items) if items else 0.0
    false_positive_rate_clean = clean_false_positive / clean_total if clean_total else 0.0
    overcorrection_rate = clean_changed / clean_total if clean_total else 0.0

    manual_change_rate = manual_changed / manual_total if manual_total else 0.0
    manual_clean_change_rate = manual_clean_changes / manual_total if manual_total else 0.0

    weighted_precision = (
        weighted_tp / (weighted_tp + weighted_fp) if (weighted_tp + weighted_fp) else 0.0
    )
    weighted_recall = (
        weighted_tp / (weighted_tp + weighted_fn) if (weighted_tp + weighted_fn) else 0.0
    )
    weighted_f1 = (
        2 * weighted_precision * weighted_recall / (weighted_precision + weighted_recall)
        if (weighted_precision + weighted_recall)
        else 0.0
    )

    expected_total = max(revision_items, 1)
    revision_quality = {
        "items_with_expected_revision": revision_items,
        "mean_question_similarity": question_similarity_sum / expected_total,
        "mean_option_jaccard": option_similarity_sum / expected_total,
        "exact_question_match_rate": exact_question_matches / expected_total,
        "exact_option_match_rate": exact_option_matches / expected_total,
        "exact_revision_rate": exact_revision_count / expected_total,
        "revision_changed_rate": changed_count / expected_total,
    }

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
        "manual_review": {
            "items_flagged_for_review": manual_total,
            "items_flagged_and_changed": manual_changed,
            "items_flagged_change_rate": manual_change_rate,
            "flagged_clean_items_changed": manual_clean_changes,
            "flagged_clean_items_change_rate": manual_clean_change_rate,
        },
        "revision_quality": revision_quality,
        "severity_weighted": {
            "enabled": bool(use_severity_weighting),
            "precision": weighted_precision,
            "recall": weighted_recall,
            "f1": weighted_f1,
            "tp_weighted": weighted_tp,
            "fp_weighted": weighted_fp,
            "fn_weighted": weighted_fn,
            "category_weights": CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY
            if use_severity_weighting
            else {},
        },
        "by_category": {cat: dict(counts) for cat, counts in sorted(by_category.items())},
    }
