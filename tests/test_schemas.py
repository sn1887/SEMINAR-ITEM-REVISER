from item_reviser.schemas import (
    OrchestrationTrace,
    PipelineError,
    PipelineResult,
    RevisedItem,
    SurveyItem,
)


def test_survey_item_roundtrip():
    data = {"id": "x", "question": "Q?", "response_options": ["Yes", "No"], "known_errors": []}
    item = SurveyItem.from_dict(data)
    assert item.to_dict()["id"] == "x"
    assert item.response_options == ["Yes", "No"]


def test_pipeline_result_serializes_optional_orchestration_trace():
    item = SurveyItem(id="x", question="Q?")
    trace = OrchestrationTrace(
        orchestration_enabled=True,
        route="accept",
        router_decision="accept",
        taxonomy_labels=[],
        confidence=0.95,
        selected_agent="accept",
        validation_status="pass",
        final_status="accepted",
    )
    result = PipelineResult(
        item_id=item.id,
        original_item=item,
        detected_errors=[],
        revised_item=RevisedItem(question=item.question, changed=False),
        orchestration_trace=trace,
    )

    data = result.to_dict()

    assert data["orchestration_trace"]["route"] == "accept"
    assert data["orchestration"]["final_status"] == "accepted"


def test_pipeline_result_serializes_evaluation_error():
    item = SurveyItem(id="x", question="Q?")
    result = PipelineResult(
        item_id=item.id,
        original_item=item,
        detected_errors=[],
        revised_item=RevisedItem(question=item.question, changed=False),
        error=PipelineError(
            error_type="LLMOutputParseError",
            message="Invalid JSON",
            stage="pipeline.run",
        ),
    )

    data = result.to_dict()

    assert data["error"]["error_type"] == "LLMOutputParseError"
    assert data["error"]["stage"] == "pipeline.run"
