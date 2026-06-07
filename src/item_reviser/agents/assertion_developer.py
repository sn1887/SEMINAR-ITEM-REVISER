from __future__ import annotations

from item_reviser.agents.base import BaseAgent


class AssertionDeveloperAgent(BaseAgent):
    """Stub for assertion formulation component."""

    def develop(self, indicator: str) -> str:
        return f"Respondent has an opinion about {indicator}."
