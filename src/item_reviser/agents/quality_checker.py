from __future__ import annotations

from item_reviser.agents.base import BaseAgent
from item_reviser.checks.registry import run_all_checks
from item_reviser.schemas import CheckResult, SurveyItem


class QualityCheckerAgent(BaseAgent):
    """Hybrid quality checker.

    Current baseline uses deterministic checks. The LLM model is held here so later
    work can add LLM validation or LLM-only checks without changing evaluation code.
    """

    def check(self, item: SurveyItem) -> list[CheckResult]:
        return run_all_checks(item)
