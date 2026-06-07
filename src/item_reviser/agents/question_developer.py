from __future__ import annotations

from item_reviser.agents.base import BaseAgent
from item_reviser.schemas import SurveyItem


class QuestionDeveloperAgent(BaseAgent):
    """Stub for question-development component."""

    def develop(self, assertion: str) -> SurveyItem:
        return SurveyItem(question=f"To what extent do you agree with the following statement: {assertion}")
