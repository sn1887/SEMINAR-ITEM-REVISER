from __future__ import annotations

import json

from item_reviser.agents.base import BaseAgent
from item_reviser.constants import CATEGORY_DESCRIPTIONS, ERROR_CATEGORIES
from item_reviser.models.base import CHECKER_OUTPUT_SCHEMA, BaseLLM
from item_reviser.prompting import AgentPromptConfig
from item_reviser.schemas import CheckResult, SurveyItem


class QualityCheckerAgent(BaseAgent):
    """LLM-backed quality checker for questionnaire-design problems."""

    def __init__(self, model: BaseLLM, prompt_config: object) -> None:
        if model is None:
            raise ValueError("QualityCheckerAgent requires an LLM model.")
        super().__init__(model=model)
        self.prompt_config = AgentPromptConfig.from_config(prompt_config)

    def check(self, item: SurveyItem) -> list[CheckResult]:
        prompt = self.prompt_config.render(
            {
                "allowed_categories": _format_allowed_categories(),
                "output_schema": CHECKER_OUTPUT_SCHEMA,
                "item_id": item.id,
                "question": item.question,
                "response_options": item.response_options,
                "target_concept": item.target_concept or "unknown",
                "topic": item.topic or "unknown",
            }
        )
        payload = self.model.complete_checker_output(
            prompt,
            max_retries=self.prompt_config.max_retries,
            timeout_seconds=self.prompt_config.timeout_seconds,
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


def _format_allowed_categories() -> str:
    rows = [
        {
            "category": category,
            "description": CATEGORY_DESCRIPTIONS.get(category, ""),
        }
        for category in ERROR_CATEGORIES
    ]
    return json.dumps(rows, ensure_ascii=False, indent=2)
