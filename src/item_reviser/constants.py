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
