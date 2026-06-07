from __future__ import annotations

import re

from item_reviser.checks.base import BaseChecker
from item_reviser.schemas import CheckResult, SurveyItem

POSITIVE_WORDS = ["agree", "satisfied", "good", "support", "approve", "important", "positive", "very satisfied"]
NEGATIVE_WORDS = ["disagree", "dissatisfied", "bad", "oppose", "disapprove", "unimportant", "negative", "very dissatisfied"]


class ScaleChecker(BaseChecker):
    name = "scale"

    def check(self, item: SurveyItem) -> list[CheckResult]:
        results: list[CheckResult] = []
        options = [str(o).strip() for o in item.response_options if str(o).strip()]
        q = item.question.lower()

        if self._is_agree_disagree(q, options):
            results.append(
                CheckResult(
                    category="agree_disagree_scale",
                    severity="medium",
                    explanation="The item uses agree/disagree response options; item-specific response scales are often clearer and reduce an extra translation step.",
                    evidence=" | ".join(options) if options else item.question,
                    suggestion="Ask directly for the target judgment using item-specific options.",
                    checker=self.name,
                )
            )

        if options and self._is_unbalanced(options):
            results.append(
                CheckResult(
                    category="unbalanced_scale",
                    severity="high",
                    explanation="The response categories do not provide balanced positive and negative alternatives.",
                    evidence=" | ".join(options),
                    suggestion="Use symmetric response categories around a neutral point if the concept is bipolar.",
                    checker=self.name,
                )
            )

        if options and self._has_incomplete_options(item, options):
            results.append(
                CheckResult(
                    category="incomplete_options",
                    severity="high",
                    explanation="The closed response categories omit plausible answers.",
                    evidence=" | ".join(options),
                    suggestion="Add missing categories or an 'Other, please specify' option where appropriate.",
                    checker=self.name,
                )
            )

        if options and self._has_nonexclusive_options(options):
            results.append(
                CheckResult(
                    category="non_exclusive_options",
                    severity="high",
                    explanation="Some response categories overlap, so respondents may fit more than one option.",
                    evidence=" | ".join(options),
                    suggestion="Use mutually exclusive boundaries, e.g. 18–24, 25–34.",
                    checker=self.name,
                )
            )

        if self._missing_scale_labels(item, options):
            results.append(
                CheckResult(
                    category="missing_scale_labels",
                    severity="medium",
                    explanation="The scale uses numbers without clear verbal labels or endpoint definitions.",
                    evidence=" | ".join(options) if options else item.question,
                    suggestion="Label at least the endpoints and preferably all categories when feasible.",
                    checker=self.name,
                )
            )

        if self._too_many_points(item, options):
            results.append(
                CheckResult(
                    category="too_many_scale_points",
                    severity="low",
                    explanation="The scale has more than 11 points, which may add noise for many survey tasks.",
                    evidence=" | ".join(options) if options else item.question,
                    suggestion="Consider a 5-, 7-, or 11-point scale depending on the concept and mode.",
                    checker=self.name,
                )
            )

        if self._polarity_mismatch(q, options):
            results.append(
                CheckResult(
                    category="polarity_mismatch",
                    severity="medium",
                    explanation="The question wording suggests a bipolar concept, but the response scale does not include both poles.",
                    evidence=" | ".join(options),
                    suggestion="Use a bipolar scale if the concept is bipolar.",
                    checker=self.name,
                )
            )

        return results

    @staticmethod
    def _is_agree_disagree(q: str, options: list[str]) -> bool:
        if "agree or disagree" in q:
            return True
        joined = " ".join(o.lower() for o in options)
        return "agree" in joined and "disagree" in joined

    @staticmethod
    def _is_unbalanced(options: list[str]) -> bool:
        lower = [o.lower() for o in options]
        pos = 0
        neg = 0
        for opt in lower:
            # Count negative first so "dissatisfied" is not also counted as "satisfied".
            if any(w in opt for w in NEGATIVE_WORDS):
                neg += 1
            elif any(w in opt for w in POSITIVE_WORDS):
                pos += 1
        # Ignore pure yes/no.
        if set(lower) <= {"yes", "no", "don't know", "prefer not to answer"}:
            return False
        return abs(pos - neg) >= 2 and (pos > 0 or neg > 0)

    @staticmethod
    def _has_incomplete_options(item: SurveyItem, options: list[str]) -> bool:
        q = item.question.lower()
        lower = [o.lower() for o in options]
        joined = " ".join(lower)
        if "destination" in q and {"beach", "city"}.issubset(set(lower)) and "other" not in joined:
            return True
        if "pet" in q and "dog" in joined and "cat" in joined and "other" not in joined:
            return True
        if "news" in q and "every day" in joined and "never" in joined and "sometimes" not in joined:
            return True
        return False

    @staticmethod
    def _has_nonexclusive_options(options: list[str]) -> bool:
        ranges: list[tuple[int, int]] = []
        for opt in options:
            nums = [int(n) for n in re.findall(r"\d+", opt)]
            if len(nums) >= 2:
                lo, hi = nums[0], nums[1]
                if lo <= hi:
                    ranges.append((lo, hi))
        for i, (lo1, hi1) in enumerate(ranges):
            for lo2, hi2 in ranges[i + 1 :]:
                if max(lo1, lo2) <= min(hi1, hi2):
                    return True
        return False

    @staticmethod
    def _missing_scale_labels(item: SurveyItem, options: list[str]) -> bool:
        if options and all(re.fullmatch(r"-?\d+", o) for o in options) and len(options) >= 3:
            return True
        q = item.question.lower()
        numeric_range = re.search(r"\b(0|1)\s*(to|-)\s*(10|100)\b", q)
        has_endpoint_label = any(phrase in q for phrase in ["where 0", "where 1", "means", "not at all", "completely"])
        return bool(numeric_range and not has_endpoint_label)

    @staticmethod
    def _too_many_points(item: SurveyItem, options: list[str]) -> bool:
        if len(options) > 11:
            return True
        q = item.question.lower()
        m = re.search(r"\b(0|1)\s*(?:to|-)\s*(\d{2,3})\b", q)
        if m:
            upper = int(m.group(2))
            return upper > 11
        return False

    @staticmethod
    def _polarity_mismatch(q: str, options: list[str]) -> bool:
        if not options:
            return False
        lower = " ".join(o.lower() for o in options)
        bipolar_question = any(phrase in q for phrase in ["satisfied or dissatisfied", "good or bad", "support or oppose", "positive or negative"])
        has_positive = any(w in lower for w in POSITIVE_WORDS)
        has_negative = any(w in lower for w in NEGATIVE_WORDS)
        return bipolar_question and not (has_positive and has_negative)
