import json

import pytest

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.models.base import BaseLLM
from item_reviser.schemas import SurveyItem


class QueueLLM(BaseLLM):
    backend_name = "queue"

    def __init__(self, responses: list[dict[str, object]]) -> None:
        super().__init__()
        self.responses = list(responses)

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs,
    ) -> str:
        _ = prompt, timeout_seconds, kwargs
        return json.dumps(self.responses.pop(0))


def test_llm_pipeline_detects_and_revises_item():
    model = QueueLLM(
        [
            {
                "errors": [
                    {
                        "category": "leading_question",
                        "severity": "high",
                        "explanation": "The question cues agreement.",
                        "evidence": "Don't you agree",
                    }
                ]
            },
            {
                "question": "To what extent do you support or oppose stricter rules?",
                "response_options": [
                    "Strongly oppose",
                    "Somewhat oppose",
                    "Neither support nor oppose",
                    "Somewhat support",
                    "Strongly support",
                ],
                "revision_notes": ["Removed leading wording."],
                "changed": True,
            },
        ]
    )
    item = SurveyItem(question="Don't you agree that stricter rules are needed?")

    result = ItemReviserPipeline(model=model).run(item)

    assert result.predicted_categories() == ["leading_question"]
    assert result.revised_item.changed is True
    assert "support or oppose" in result.revised_item.question


def test_pipeline_requires_model():
    with pytest.raises(ValueError, match="requires an LLM model"):
        ItemReviserPipeline(model=None)  # type: ignore[arg-type]
