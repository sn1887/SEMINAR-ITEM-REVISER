from __future__ import annotations

from item_reviser.agents.base import BaseAgent
from item_reviser.schemas import CheckResult, RevisedItem, SurveyItem

BALANCED_SUPPORT_SCALE = [
    "Strongly oppose",
    "Somewhat oppose",
    "Neither support nor oppose",
    "Somewhat support",
    "Strongly support",
]

BALANCED_SATISFACTION_SCALE = [
    "Very dissatisfied",
    "Somewhat dissatisfied",
    "Neither satisfied nor dissatisfied",
    "Somewhat satisfied",
    "Very satisfied",
]

FREQUENCY_SCALE = ["Never", "Rarely", "Sometimes", "Often", "Very often"]


class ItemReviserAgent(BaseAgent):
    """Simple deterministic reviser baseline.

    Later, this can call an LLM using prompts/agents/item_reviser.md.
    """

    def revise(self, item: SurveyItem, errors: list[CheckResult]) -> RevisedItem:
        categories = {e.category for e in errors}
        if not categories:
            return RevisedItem(
                question=item.question,
                response_options=item.response_options,
                revision_notes=["No errors detected; item left unchanged."],
                changed=False,
            )

        q = item.question.strip()
        opts = list(item.response_options)
        notes: list[str] = []

        if "leading_question" in categories:
            q = self._neutralize_leading(q, item)
            opts = self._default_scale_for_question(q, opts)
            notes.append("Neutralized leading wording and used balanced options.")

        if "loaded_question" in categories:
            q = self._remove_loaded_assumption(q)
            notes.append("Removed or softened implicit assumption.")

        if "double_barreled" in categories:
            q = self._split_signal(q)
            notes.append("Marked item for splitting because it asks about multiple concepts.")

        if "recall_error" in categories:
            q = self._shorten_reference_period(q)
            if not opts:
                opts = FREQUENCY_SCALE
            notes.append("Shortened reference period or broadened recall task.")

        if "vague_ambiguous" in categories:
            q = self._make_more_specific(q)
            notes.append("Replaced vague wording with a more specific formulation.")

        if "sensitive_topic_direct" in categories or "social_desirability" in categories:
            q = self._soften_sensitive(q)
            notes.append("Added normalization/less judgmental wording for sensitive topic.")

        if "negative_wording" in categories:
            q = self._remove_negatives(q)
            notes.append("Rewrote negative wording in a more direct form.")

        scale_categories = {
            "agree_disagree_scale",
            "unbalanced_scale",
            "incomplete_options",
            "non_exclusive_options",
            "missing_scale_labels",
            "too_many_scale_points",
            "polarity_mismatch",
            "open_closed_mismatch",
        }
        if categories & scale_categories:
            opts = self._default_scale_for_question(q, opts)
            notes.append("Revised response options according to scale-design issue.")

        return RevisedItem(question=q, response_options=opts, revision_notes=notes, changed=True)

    @staticmethod
    def _neutralize_leading(q: str, item: SurveyItem) -> str:
        lower = q.lower()
        if "environmental" in lower:
            return "To what extent do you support or oppose stricter environmental regulations?"
        if "elderly" in lower:
            return "To what extent do you think society should or should not provide more support for older people?"
        if item.target_concept:
            return f"What is your view about {item.target_concept}?"
        return q.replace("Don’t you agree that ", "To what extent do you agree or disagree that ").replace("don't you agree that ", "To what extent do you agree or disagree that ")

    @staticmethod
    def _remove_loaded_assumption(q: str) -> str:
        lower = q.lower()
        if lower.startswith("what is the best book"):
            return "Did you read any books last year? If yes, which book did you like most?"
        if lower.startswith("whom did you vote for"):
            return "Did you vote in the last election? If yes, which party or candidate did you vote for?"
        if lower.startswith("where do you like to exercise"):
            return "Do you exercise? If yes, where do you usually exercise?"
        return q

    @staticmethod
    def _split_signal(q: str) -> str:
        return f"This item should be split into separate questions: {q}"

    @staticmethod
    def _shorten_reference_period(q: str) -> str:
        q = q.replace("in the last month", "yesterday")
        q = q.replace("during the last month", "yesterday")
        q = q.replace("in the past year", "during the last 7 days")
        q = q.replace("during the past year", "during the last 7 days")
        q = q.replace("last 12 months", "last 7 days")
        return q

    @staticmethod
    def _make_more_specific(q: str) -> str:
        q = q.replace("regularly", "at least three times per week")
        q = q.replace("often", "how frequently")
        q = q.replace("good service", "service that meets your expectations")
        return q

    @staticmethod
    def _soften_sensitive(q: str) -> str:
        if "copied" in q.lower() or "plagiar" in q.lower():
            return "Students sometimes copy text or answers when under time pressure. During the current semester, how often, if at all, have you copied text or answers without proper attribution?"
        if "vote" in q.lower():
            return "Some people do not vote for different reasons. Which of the following best describes whether you voted in the last election?"
        if "prejudiced" in q.lower():
            return "How comfortable or uncomfortable would you feel interacting with transgender people in everyday situations?"
        return q

    @staticmethod
    def _remove_negatives(q: str) -> str:
        q = q.replace("It is not important to me that", "How important is it to you that")
        q = q.replace("I usually do not have", "I usually have")
        q = q.replace("not", "")
        return " ".join(q.split())

    @staticmethod
    def _default_scale_for_question(q: str, current: list[str]) -> list[str]:
        lower = q.lower()
        if "satisfied" in lower or "dissatisfied" in lower:
            return BALANCED_SATISFACTION_SCALE
        if "how often" in lower or "how frequently" in lower:
            return FREQUENCY_SCALE
        if "support" in lower or "oppose" in lower or "regulation" in lower:
            return BALANCED_SUPPORT_SCALE
        if "age" in lower:
            return ["18–24", "25–34", "35–44", "45–54", "55–64", "65 or older"]
        if current and len(current) <= 7:
            return current
        return ["Very negative", "Somewhat negative", "Neither negative nor positive", "Somewhat positive", "Very positive"]
