from __future__ import annotations

ERROR_CATEGORIES = [
    "leading_question",
    "loaded_question",
    "double_barreled",
    "recall_error",
    "vague_ambiguous",
    "sensitive_topic_direct",
    "social_desirability",
    "negative_wording",
    "open_closed_mismatch",
    "agree_disagree_scale",
    "unbalanced_scale",
    "incomplete_options",
    "non_exclusive_options",
    "missing_scale_labels",
    "too_many_scale_points",
    "polarity_mismatch",
]

DATASET_SCHEMA_VERSION = "1.0.0"

CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY = {
    "leading_question": 1.0,
    "loaded_question": 1.0,
    "double_barreled": 1.0,
    "recall_error": 0.7,
    "vague_ambiguous": 0.7,
    "sensitive_topic_direct": 0.7,
    "social_desirability": 0.7,
    "negative_wording": 0.7,
    "open_closed_mismatch": 0.4,
    "agree_disagree_scale": 0.7,
    "unbalanced_scale": 0.7,
    "incomplete_options": 0.7,
    "non_exclusive_options": 0.4,
    "missing_scale_labels": 0.4,
    "too_many_scale_points": 0.4,
    "polarity_mismatch": 0.4,
}


CATEGORY_DESCRIPTIONS = {
    "leading_question": "Wording suggests a preferred answer.",
    "loaded_question": "Question presupposes something that may not be true.",
    "double_barreled": "One request asks about more than one concept.",
    "recall_error": "Reference period or task makes accurate recall unlikely.",
    "vague_ambiguous": "Key concepts are undefined, subjective, or unclear.",
    "sensitive_topic_direct": "Sensitive topic asked too directly.",
    "social_desirability": "Item likely encourages norm-conforming answers.",
    "negative_wording": "Negatives or double negatives may confuse respondents.",
    "open_closed_mismatch": "Open/closed format does not match the measurement goal.",
    "agree_disagree_scale": "Agree/disagree scale used where item-specific options are preferable.",
    "unbalanced_scale": "Response options favor one side of the scale.",
    "incomplete_options": "Closed response options omit plausible categories.",
    "non_exclusive_options": "Single-choice response options overlap.",
    "missing_scale_labels": "Numeric scale lacks meaningful labels.",
    "too_many_scale_points": "Scale has more points than recommended for most survey contexts.",
    "polarity_mismatch": "Concept polarity and response scale polarity are misaligned.",
}
