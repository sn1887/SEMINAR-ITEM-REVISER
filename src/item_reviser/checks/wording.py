from __future__ import annotations

import re

from item_reviser.checks.base import BaseChecker
from item_reviser.schemas import CheckResult, SurveyItem


class WordingChecker(BaseChecker):
    name = "wording"

    def check(self, item: SurveyItem) -> list[CheckResult]:
        q = item.question.strip()
        q_lower = q.lower()
        results: list[CheckResult] = []

        if self._is_leading(q_lower):
            results.append(
                CheckResult(
                    category="leading_question",
                    severity="high",
                    explanation="The item wording suggests that one answer is expected or more appropriate.",
                    evidence=q,
                    suggestion="Use neutral wording and balanced response options.",
                    checker=self.name,
                )
            )

        if self._is_loaded(q_lower):
            results.append(
                CheckResult(
                    category="loaded_question",
                    severity="high",
                    explanation="The item presupposes a condition or behavior that may not apply to all respondents.",
                    evidence=q,
                    suggestion="Use a screening question or remove the implicit assumption.",
                    checker=self.name,
                )
            )

        if self._is_double_barreled(q_lower):
            results.append(
                CheckResult(
                    category="double_barreled",
                    severity="high",
                    explanation="The item appears to ask about multiple concepts or objects in one request.",
                    evidence=q,
                    suggestion="Split the item into separate questions, one concept per item.",
                    checker=self.name,
                )
            )

        if self._has_recall_problem(q_lower):
            results.append(
                CheckResult(
                    category="recall_error",
                    severity="medium",
                    explanation="The requested recall period or level of detail may be difficult for respondents to remember accurately.",
                    evidence=q,
                    suggestion="Use a shorter reference period or broader response categories.",
                    checker=self.name,
                )
            )

        if self._is_vague(q_lower):
            results.append(
                CheckResult(
                    category="vague_ambiguous",
                    severity="medium",
                    explanation="Key terms are subjective or undefined, which may lead respondents to interpret the item differently.",
                    evidence=q,
                    suggestion="Define the key term or use a more specific item.",
                    checker=self.name,
                )
            )

        if self._is_sensitive_direct(q_lower):
            results.append(
                CheckResult(
                    category="sensitive_topic_direct",
                    severity="medium",
                    explanation="The item asks about a sensitive topic in a direct way that may increase nonresponse or socially desirable answers.",
                    evidence=q,
                    suggestion="Consider normalization, confidentiality reminders, ranges, or self-completion mode.",
                    checker=self.name,
                )
            )

        if self._has_social_desirability(q_lower):
            results.append(
                CheckResult(
                    category="social_desirability",
                    severity="medium",
                    explanation="The item concerns behavior with a strong social norm and may lead to over- or under-reporting.",
                    evidence=q,
                    suggestion="Normalize the behavior or use less judgmental wording.",
                    checker=self.name,
                )
            )

        if self._has_negative_wording(q_lower):
            results.append(
                CheckResult(
                    category="negative_wording",
                    severity="medium",
                    explanation="Negative wording or double negatives may be overlooked and confuse respondents.",
                    evidence=q,
                    suggestion="Rewrite in positive, direct wording.",
                    checker=self.name,
                )
            )

        if self._open_closed_mismatch(item):
            results.append(
                CheckResult(
                    category="open_closed_mismatch",
                    severity="low",
                    explanation="The item appears open-ended although the measurement goal likely requires a closed or scaled response.",
                    evidence=q,
                    suggestion="Use a closed item-specific scale if the goal is comparable measurement.",
                    checker=self.name,
                )
            )

        return results

    @staticmethod
    def _is_leading(q: str) -> bool:
        patterns = [
            r"don[’']?t you agree",
            r"wouldn[’']?t you agree",
            r"surely",
            r"obviously",
            r"clearly",
            r"should society do more",
            r"do you think .* should do more",
            r"what makes .* better than",
            r"how much do you support the necessary",
        ]
        return any(re.search(p, q) for p in patterns)

    @staticmethod
    def _is_loaded(q: str) -> bool:
        patterns = [
            r"what is the best .* you",
            r"whom did you vote for",
            r"where do you like to",
            r"how often do you still",
            r"do you want to continue",
            r"why do you oppose",
            r"why did you fail",
        ]
        return any(re.search(p, q) for p in patterns)

    @staticmethod
    def _is_double_barreled(q: str) -> bool:
        multi_object_patterns = [
            r"\b(and|or)\b.*\b(and|or)\b",
            r"health system and (its )?medical staff",
            r"quality and comparability",
            r"satisfied with .* and .*",
            r"support .* and oppose .*",
            r"allowed .* but should",
            r"prepared .* and .* consequences",
        ]
        return any(re.search(p, q) for p in multi_object_patterns)

    @staticmethod
    def _has_recall_problem(q: str) -> bool:
        long_period = any(phrase in q for phrase in ["last month", "last year", "past year", "past 12 months", "last 12 months"])
        detailed = any(phrase in q for phrase in ["how many hours", "how many minutes", "exactly", "how many times"])
        frequent = any(phrase in q for phrase in ["social media", "watch", "exercise", "news", "coffee", "snacks"])
        return long_period and (detailed or frequent)

    @staticmethod
    def _is_vague(q: str) -> bool:
        vague_terms = [
            "regularly",
            "often",
            "frequently",
            "good service",
            "healthy food",
            "successful",
            "reasonable amount",
            "normal amount",
            "high quality",
        ]
        if any(term in q for term in vague_terms):
            return True
        return bool(re.search(r"how (good|bad|successful|important) is (it|this|that)\??$", q))

    @staticmethod
    def _is_sensitive_direct(q: str) -> bool:
        sensitive_terms = [
            "prejudiced against",
            "transgender people",
            "income",
            "illegal drugs",
            "stolen",
            "plagiarized",
            "copied from someone",
            "sexual partners",
            "abortion",
            "mental health",
        ]
        return any(term in q for term in sensitive_terms)

    @staticmethod
    def _has_social_desirability(q: str) -> bool:
        topics = [
            "did you vote",
            "donated to charity",
            "volunteer",
            "illegal drugs",
            "stolen",
            "plagiarized",
            "exercise",
            "healthy diet",
        ]
        return any(topic in q for topic in topics)

    @staticmethod
    def _has_negative_wording(q: str) -> bool:
        if re.search(r"\bnot\b.{0,40}\b(not|never|no|without)\b", q):
            return True
        patterns = [
            r"not important",
            r"do you disagree.*not",
            r"should not .* without",
            r"isn[’']?t it true",
        ]
        return any(re.search(p, q) for p in patterns)

    @staticmethod
    def _open_closed_mismatch(item: SurveyItem) -> bool:
        q = item.question.lower()
        if item.response_options:
            return False
        return q.startswith("what do you think about") or q.startswith("how do you feel about")
