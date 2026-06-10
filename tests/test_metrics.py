from item_reviser.evaluation.metrics import compute_detection_metrics
from item_reviser.schemas import CheckResult, PipelineResult, RevisedItem, SurveyItem


def test_metrics_smoke():
    items = [
        SurveyItem(
            id="1",
            question="Don’t you agree that X is good?",
            known_errors=["leading_question"],
        ),
        SurveyItem(
            id="2",
            question="How satisfied or dissatisfied are you with your job?",
            response_options=[
                "Very dissatisfied",
                "Somewhat dissatisfied",
                "Neither satisfied nor dissatisfied",
                "Somewhat satisfied",
                "Very satisfied",
            ],
            known_errors=[],
        ),
    ]
    results = [
        PipelineResult(
            item_id="1",
            original_item=items[0],
            detected_errors=[
                CheckResult(
                    category="leading_question",
                    severity="high",
                    explanation="The item suggests agreement is expected.",
                )
            ],
            revised_item=RevisedItem(
                question="To what extent do you think X is good?",
                response_options=[],
                changed=True,
            ),
        ),
        PipelineResult(
            item_id="2",
            original_item=items[1],
            detected_errors=[],
            revised_item=RevisedItem(
                question=items[1].question,
                response_options=items[1].response_options,
                changed=False,
            ),
        ),
    ]
    metrics = compute_detection_metrics(items, results)
    assert metrics["num_items"] == 2
    assert "precision" in metrics
