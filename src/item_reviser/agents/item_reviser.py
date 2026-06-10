from __future__ import annotations

import json

from item_reviser.agents.base import BaseAgent
from item_reviser.constants import CATEGORY_DESCRIPTIONS, ERROR_CATEGORIES
from item_reviser.models.base import BaseLLM, REVISER_OUTPUT_SCHEMA
from item_reviser.prompting import AgentPromptConfig
from item_reviser.schemas import CheckResult, RevisedItem, SurveyItem


class ItemReviserAgent(BaseAgent):
    """LLM-backed item reviser."""

    def __init__(self, model: BaseLLM, prompt_config: object) -> None:
        if model is None:
            raise ValueError("ItemReviserAgent requires an LLM model.")
        super().__init__(model=model)
        self.prompt_config = AgentPromptConfig.from_config(prompt_config)

    def revise(self, item: SurveyItem, errors: list[CheckResult]) -> RevisedItem:
        prompt = self._build_reviser_prompt(item, errors)
        payload = self.model.complete_reviser_output(
            prompt,
            max_retries=self.prompt_config.max_retries,
            timeout_seconds=self.prompt_config.timeout_seconds,
        )
        return self._from_payload(item, payload)

    def _build_reviser_prompt(self, item: SurveyItem, errors: list[CheckResult]) -> str:
        categories = sorted({e.category for e in errors})
        return self.prompt_config.render(
            {
                "allowed_categories": _format_allowed_categories(),
                "output_schema": REVISER_OUTPUT_SCHEMA,
                "item_id": item.id,
                "question": item.question,
                "response_options": item.response_options,
                "target_concept": item.target_concept or "unknown",
                "topic": item.topic or "unknown",
                "detected_categories": categories,
                "detected_issues": [error.to_dict() for error in errors],
            }
        )

    @staticmethod
    def _from_payload(item: SurveyItem, payload: dict[str, object]) -> RevisedItem:
        question = str(payload.get("question", item.question)).strip()
        response_options = payload.get("response_options", item.response_options)
        if not isinstance(response_options, list):
            response_options = item.response_options
        revision_notes = payload.get("revision_notes", ["LLM revision provided"])
        if isinstance(revision_notes, str):
            revision_notes = [revision_notes]
        if not isinstance(revision_notes, list):
            revision_notes = ["LLM revision provided"]
        changed = bool(payload.get("changed", True))
        return RevisedItem(
            question=question,
            response_options=[str(x) for x in response_options],
            revision_notes=[str(note) for note in revision_notes],
            changed=changed,
        )


def _format_allowed_categories() -> str:
    rows = [
        {
            "category": category,
            "description": CATEGORY_DESCRIPTIONS.get(category, ""),
        }
        for category in ERROR_CATEGORIES
    ]
    return json.dumps(rows, ensure_ascii=False, indent=2)
