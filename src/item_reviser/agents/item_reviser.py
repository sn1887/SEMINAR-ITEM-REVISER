from __future__ import annotations

from item_reviser.agents.base import BaseAgent
from item_reviser.constants import ERROR_CATEGORIES
from item_reviser.models.base import BaseLLM, REVISER_OUTPUT_SCHEMA
from item_reviser.schemas import CheckResult, RevisedItem, SurveyItem


class ItemReviserAgent(BaseAgent):
    """LLM-backed item reviser."""

    def __init__(self, model: BaseLLM) -> None:
        if model is None:
            raise ValueError("ItemReviserAgent requires an LLM model.")
        super().__init__(model=model)
        self._prompt_template = (
            "You are a survey-revision assistant.\n"
            "Revise the item to fix quality issues in the JSON schema shown below.\n"
            "Do not add explanations outside JSON.\n"
            f"{REVISER_OUTPUT_SCHEMA}\n"
            "Allowed error categories: "
            + ", ".join(sorted(ERROR_CATEGORIES))
            + "\n"
        )

    def revise(self, item: SurveyItem, errors: list[CheckResult]) -> RevisedItem:
        prompt = self._build_reviser_prompt(item, errors)
        payload = self.model.complete_reviser_output(
            prompt,
            max_retries=3,
            timeout_seconds=120.0,
        )
        return self._from_payload(item, payload)

    def _build_reviser_prompt(self, item: SurveyItem, errors: list[CheckResult]) -> str:
        categories = sorted({e.category for e in errors})
        notes = (
            [f"- {error.category}: {error.explanation}" for error in errors]
            if errors
            else ["No detected issues."]
        )
        return (
            f"{self._prompt_template}\n"
            "Context:\n"
            f"question: {item.question}\n"
            f"response_options: {item.response_options}\n"
            f"target_concept: {item.target_concept or 'unknown'}\n"
            f"topic: {item.topic or 'unknown'}\n"
            f"detected_categories: {categories}\n"
            "Known issues:\n"
            + "\n".join(notes)
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
