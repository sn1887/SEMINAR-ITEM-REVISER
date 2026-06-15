import json

import pytest

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.models.base import BaseLLM
from item_reviser.schemas import SurveyItem


TEST_PROMPT_CONFIG = {
    "quality_checker": {
        "template": "Check this item: ${question}",
        "max_retries": 2,
        "timeout_seconds": 10,
    },
    "item_reviser": {
        "template": "Revise this item: ${question}\nIssues: ${detected_issues}",
        "max_retries": 2,
        "timeout_seconds": 10,
    },
}


class QueueLLM(BaseLLM):
    backend_name = "queue"

    def __init__(self, responses: list[dict[str, object]]) -> None:
        super().__init__()
        self.responses = list(responses)
        self.calls = 0

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs,
    ) -> str:
        _ = prompt, timeout_seconds, kwargs
        self.calls += 1
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

    result = ItemReviserPipeline(model=model, prompt_config=TEST_PROMPT_CONFIG).run(item)

    assert result.predicted_categories() == ["leading_question"]
    assert result.revised_item.changed is True
    assert "support or oppose" in result.revised_item.question
    assert result.orchestration_trace is None
    assert "orchestration" not in result.to_dict()
    assert model.calls == 2


def test_llm_pipeline_skips_reviser_when_no_issues_are_detected():
    model = QueueLLM([{"errors": []}])
    item = SurveyItem(
        question="How satisfied or dissatisfied are you with your current job?",
        response_options=[
            "Very dissatisfied",
            "Somewhat dissatisfied",
            "Neither satisfied nor dissatisfied",
            "Somewhat satisfied",
            "Very satisfied",
        ],
    )

    result = ItemReviserPipeline(model=model, prompt_config=TEST_PROMPT_CONFIG).run(item)

    assert result.predicted_categories() == []
    assert result.revised_item.question == item.question
    assert result.revised_item.response_options == item.response_options
    assert result.revised_item.changed is False
    assert result.revised_item.revision_notes == ["No issues detected; item left unchanged."]
    assert model.calls == 1


def test_llm_pipeline_can_force_revision_even_without_detected_issues_via_config():
    model = QueueLLM(
        [
            {"errors": []},
            {
                "question": "How satisfied are you with your current job?",
                "response_options": [
                    "Very dissatisfied",
                    "Somewhat dissatisfied",
                    "Neither satisfied nor dissatisfied",
                    "Somewhat satisfied",
                    "Very satisfied",
                ],
                "revision_notes": ["Tightened wording."],
                "changed": True,
            },
        ]
    )
    item = SurveyItem(
        question="How satisfied or dissatisfied are you with your current job?",
        response_options=[
            "Very dissatisfied",
            "Somewhat dissatisfied",
            "Neither satisfied nor dissatisfied",
            "Somewhat satisfied",
            "Very satisfied",
        ],
    )

    result = ItemReviserPipeline(
        model=model,
        prompt_config=TEST_PROMPT_CONFIG,
        agent_config={"skip_revision_when_no_errors": False},
    ).run(item)

    assert result.predicted_categories() == []
    assert result.revised_item.question == "How satisfied are you with your current job?"
    assert result.revised_item.changed is True
    assert model.calls == 2


def test_pipeline_requires_model():
    with pytest.raises(ValueError, match="requires an LLM model"):
        ItemReviserPipeline(  # type: ignore[arg-type]
            model=None,
            prompt_config=TEST_PROMPT_CONFIG,
        )
