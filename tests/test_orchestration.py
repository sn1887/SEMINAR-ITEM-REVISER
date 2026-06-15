import json

import pytest
from omegaconf import OmegaConf

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.evaluation.runner import _summarize_orchestration
from item_reviser.models.base import BaseLLM, LLMOutputSchemaError
from item_reviser.orchestration.config import OrchestrationConfig
from item_reviser.schemas import SurveyItem


def _prompt(name: str) -> dict[str, object]:
    return {
        "template": f"{name}: ${{question}}\nSchema: ${{output_schema}}",
        "max_retries": 1,
        "timeout_seconds": 10,
    }


ORCHESTRATION_PROMPTS = {
    "router": _prompt("router"),
    "revision_planner": _prompt("planner"),
    "fallback_reviser": _prompt("fallback"),
    "validator": _prompt("validator"),
    "wording_clarity": _prompt("wording"),
    "response_options_scale": _prompt("scale"),
    "construct_alignment": _prompt("construct"),
    "bias_sensitivity": _prompt("sensitivity"),
    "questionnaire_format": _prompt("format"),
}


class QueueLLM(BaseLLM):
    backend_name = "queue"

    def __init__(self, responses: list[dict[str, object]]) -> None:
        super().__init__()
        self.responses = list(responses)
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs,
    ) -> str:
        _ = timeout_seconds, kwargs
        self.prompts.append(prompt)
        return json.dumps(self.responses.pop(0))


def _router(
    decision: str,
    labels: list[str],
    *,
    confidence: float = 0.9,
    recommended_route: str = "wording_clarity",
) -> dict[str, object]:
    return {
        "decision": decision,
        "taxonomy_labels": labels,
        "confidence": confidence,
        "evidence": "evidence",
        "rationale": "rationale",
        "recommended_route": recommended_route,
    }


def _plan(family: str = "wording_clarity") -> dict[str, object]:
    return {
        "repair_family": family,
        "selected_agent": family,
        "instructions": ["Preserve the construct."],
        "rationale": "Use the selected specialist.",
    }


def _revision(question: str, *, changed: bool = True) -> dict[str, object]:
    return {
        "question": question,
        "response_options": [
            "Strongly oppose",
            "Somewhat oppose",
            "Neither support nor oppose",
            "Somewhat support",
            "Strongly support",
        ],
        "revision_notes": ["Revised by test agent."],
        "changed": changed,
        "rationale": "The candidate fixes the routed issue.",
    }


def _validator(status: str = "pass") -> dict[str, object]:
    return {
        "status": status,
        "rationale": f"Validator returned {status}.",
        "retry_instructions": ["Tighten the construct-preserving wording."]
        if status == "retry"
        else [],
        "preserves_construct": status == "pass",
        "fixes_detected_issue": status == "pass",
        "introduces_new_issue": False,
    }


def test_orchestration_config_loads_from_dictconfig_and_validates_bounds():
    cfg = OrchestrationConfig.from_config(
        OmegaConf.create(
            {
                "enabled": True,
                "confidence_threshold": 0.5,
                "retry_budget": 2,
                "routing": {"low_confidence_action": "manual_review"},
                "validation": {
                    "enabled": True,
                    "validate_accept_path": False,
                    "accept_failure_action": "manual_review",
                },
            }
        )
    )

    assert cfg.enabled is True
    assert cfg.confidence_threshold == 0.5
    assert cfg.retry_budget == 2
    assert cfg.routing.low_confidence_action == "manual_review"
    assert cfg.validation.validate_accept_path is False
    assert cfg.validation.accept_failure_action == "manual_review"
    assert cfg.family_for_label("leading_question") == "wording_clarity"

    with pytest.raises(ValueError, match="confidence_threshold"):
        OrchestrationConfig.from_config({"confidence_threshold": 1.5})

    with pytest.raises(ValueError, match="low_confidence_action"):
        OrchestrationConfig.from_config({"routing": {"low_confidence_action": "specialist"}})


def test_orchestrated_accept_path_leaves_item_unchanged_and_traced():
    model = QueueLLM([_router("accept", [], recommended_route="accept"), _validator("pass")])
    item = SurveyItem(id="clean", question="How satisfied are you?")

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True},
    ).run(item)

    assert result.detected_errors == []
    assert result.revised_item.changed is False
    assert result.orchestration_trace is not None
    assert result.orchestration_trace.route == "accept"
    assert result.to_dict()["orchestration"]["final_status"] == "accepted"
    assert _summarize_orchestration([result])["routes"]["accept"] == 1
    assert "acceptable as an unchanged questionnaire item" in model.prompts[-1]


def test_low_confidence_router_uses_fallback_reviser():
    model = QueueLLM(
        [
            _router("revise", ["leading_question"], confidence=0.2),
            _revision("To what extent do you support or oppose stricter rules?"),
            _validator("pass"),
        ]
    )
    item = SurveyItem(id="low", question="Don't you agree stricter rules are needed?")

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True, "confidence_threshold": 0.7},
    ).run(item)

    assert result.predicted_categories() == ["leading_question"]
    assert result.orchestration_trace is not None
    assert result.orchestration_trace.route == "fallback"
    assert result.orchestration_trace.selected_agent == "fallback_reviser"
    assert "support or oppose" in result.revised_item.question


def test_low_confidence_router_can_route_directly_to_manual_review():
    model = QueueLLM([_router("revise", ["leading_question"], confidence=0.2)])
    item = SurveyItem(id="manual", question="Don't you agree stricter rules are needed?")

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={
            "enabled": True,
            "routing": {"low_confidence_action": "manual_review"},
        },
    ).run(item)

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.route == "manual_review"
    assert result.orchestration_trace.final_status == "manual_review"
    assert result.revised_item.changed is False


def test_single_supported_label_uses_specialist_route():
    model = QueueLLM(
        [
            _router("revise", ["agree_disagree_scale"], recommended_route="response_options_scale"),
            _plan("response_options_scale"),
            _revision("How strongly do you support or oppose stricter rules?"),
            _validator("pass"),
        ]
    )
    item = SurveyItem(id="scale", question="Do you agree stricter rules are needed?")

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True},
    ).run(item)

    assert result.predicted_categories() == ["agree_disagree_scale"]
    assert result.orchestration_trace is not None
    assert result.orchestration_trace.route == "specialist"
    assert result.orchestration_trace.selected_agent == "response_options_scale"


def test_accept_path_validation_can_be_disabled_by_config():
    model = QueueLLM([_router("accept", [], recommended_route="accept")])
    item = SurveyItem(id="clean", question="How satisfied are you?")

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True, "validation": {"validate_accept_path": False}},
    ).run(item)

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.validation_status == "skipped"
    assert result.orchestration_trace.final_status == "accepted"
    assert len(model.prompts) == 1


def test_multi_label_cases_route_to_fallback_by_default():
    model = QueueLLM(
        [
            _router(
                "revise",
                ["leading_question", "agree_disagree_scale"],
                recommended_route="wording_clarity",
            ),
            _revision("To what extent do you support or oppose stricter rules?"),
            _validator("pass"),
        ]
    )

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True},
    ).run(SurveyItem(question="Don't you agree stricter rules are needed?"))

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.route == "fallback"
    assert "Multiple taxonomy labels" in (result.orchestration_trace.fallback_reason or "")


def test_revision_validation_can_be_disabled_by_config():
    model = QueueLLM(
        [
            _router("revise", ["leading_question"], recommended_route="fallback"),
            _revision("To what extent do you support or oppose stricter rules?"),
        ]
    )

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True, "validation": {"enabled": False}},
    ).run(SurveyItem(question="Don't you agree stricter rules are needed?"))

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.validation_status == "skipped"
    assert result.orchestration_trace.final_status == "revised"


def test_validator_retry_is_bounded_and_recorded():
    model = QueueLLM(
        [
            _router("revise", ["leading_question"], recommended_route="fallback"),
            _revision("Do you agree stricter rules are needed?"),
            _validator("retry"),
            _revision("To what extent do you support or oppose stricter rules?"),
            _validator("pass"),
        ]
    )

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True, "retry_budget": 1},
    ).run(SurveyItem(question="Don't you agree stricter rules are needed?"))

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.retry_count == 1
    assert result.orchestration_trace.validation_status == "pass"
    assert result.orchestration_trace.final_status == "revised"


def test_failed_validation_retries_while_budget_remains():
    model = QueueLLM(
        [
            _router("revise", ["leading_question"], recommended_route="fallback"),
            _revision("Do you agree stricter rules are needed?"),
            _validator("failed"),
            _revision("To what extent do you support or oppose stricter rules?"),
            _validator("pass"),
        ]
    )

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True, "retry_budget": 1},
    ).run(SurveyItem(question="Don't you agree stricter rules are needed?"))

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.retry_count == 1
    assert result.orchestration_trace.final_status == "revised"


def test_validator_manual_review_status_is_traced():
    model = QueueLLM(
        [
            _router("revise", ["leading_question"], recommended_route="fallback"),
            _revision("To what extent do you support or oppose stricter rules?"),
            _validator("manual_review"),
        ]
    )

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={"enabled": True, "retry_budget": 0},
    ).run(SurveyItem(question="Don't you agree stricter rules are needed?"))

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.route == "fallback"
    assert result.orchestration_trace.validation_status == "manual_review"
    assert result.orchestration_trace.final_status == "manual_review"


def test_out_of_range_router_confidence_is_rejected():
    model = QueueLLM([_router("accept", [], confidence=1.5, recommended_route="accept")])

    with pytest.raises(ValueError, match="confidence"):
        ItemReviserPipeline(
            model=model,
            prompt_config=ORCHESTRATION_PROMPTS,
            orchestration_config={"enabled": True},
        ).run(SurveyItem(question="Q?"))


def test_sequential_planner_family_mismatch_uses_fallback():
    model = QueueLLM(
        [
            _router(
                "revise",
                ["leading_question", "agree_disagree_scale"],
                recommended_route="wording_clarity",
            ),
            _plan("response_options_scale"),
            _revision("To what extent do you support or oppose stricter rules?"),
            _validator("pass"),
        ]
    )

    result = ItemReviserPipeline(
        model=model,
        prompt_config=ORCHESTRATION_PROMPTS,
        orchestration_config={
            "enabled": True,
            "strategy": "sequential_specialists",
            "multi_label_strategy": "sequential",
        },
    ).run(SurveyItem(question="Don't you agree stricter rules are needed?"))

    assert result.orchestration_trace is not None
    assert result.orchestration_trace.route == "fallback"
    assert result.orchestration_trace.selected_agent == "fallback_reviser"


def test_invalid_router_decision_is_rejected_by_json_schema():
    model = QueueLLM([_router("not_a_decision", [])])

    with pytest.raises(LLMOutputSchemaError):
        ItemReviserPipeline(
            model=model,
            prompt_config=ORCHESTRATION_PROMPTS,
            orchestration_config={"enabled": True},
        ).run(SurveyItem(question="Q?"))
