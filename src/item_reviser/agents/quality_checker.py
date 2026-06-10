from __future__ import annotations

from item_reviser.agents.base import BaseAgent
from item_reviser.constants import ERROR_CATEGORIES
from item_reviser.models.base import CHECKER_OUTPUT_SCHEMA, BaseLLM
from item_reviser.schemas import CheckResult, SurveyItem


class QualityCheckerAgent(BaseAgent):
    """LLM-backed quality checker for questionnaire-design problems."""

    def __init__(self, model: BaseLLM) -> None:
        if model is None:
            raise ValueError("QualityCheckerAgent requires an LLM model.")
        super().__init__(model=model)
        self._prompt_template = (
            "You are a survey-method quality checker for psychometric survey items.\n"
            "Given a survey item, return JSON matching this schema exactly:\n"
            f"{CHECKER_OUTPUT_SCHEMA}\n"
            "Only include error categories from this allowed list:\n"
            f"{', '.join(sorted(ERROR_CATEGORIES))}.\n"
            "Each detected issue should include category, severity, explanation, and optional evidence/suggestion.\n"
        )

    def check(self, item: SurveyItem) -> list[CheckResult]:
        prompt = (
            f"{self._prompt_template}\n\n"
            "Item:\n"
            f"question: {item.question}\n"
            f"response_options: {item.response_options}\n"
            f"target_concept: {item.target_concept or 'unknown'}\n"
            f"topic: {item.topic or 'unknown'}\n"
            "Return JSON with one entry per detected issue.\n"
        )
        payload = self.model.complete_checker_output(
            prompt,
            max_retries=3,
            timeout_seconds=120.0,
        )

        raw_errors = payload.get("errors", [])
        if not isinstance(raw_errors, list):
            raise ValueError("Checker model returned a non-list 'errors' field.")

        parsed: list[CheckResult] = []
        for item_error in raw_errors:
            if not isinstance(item_error, dict):
                continue
            category = str(item_error.get("category", "")).strip()
            if not category or category not in ERROR_CATEGORIES:
                continue
            parsed.append(
                CheckResult(
                    category=category,
                    severity=str(item_error.get("severity", "medium") or "medium"),
                    explanation=str(item_error.get("explanation", "") or ""),
                    evidence=(
                        str(item_error.get("evidence"))
                        if item_error.get("evidence") is not None
                        else None
                    ),
                    suggestion=(
                        str(item_error.get("suggestion"))
                        if item_error.get("suggestion") is not None
                        else None
                    ),
                    checker=str(item_error.get("checker", "llm") or "llm"),
                )
            )

        return parsed
