from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.evaluation.metrics import compute_detection_metrics
from item_reviser.schemas import SurveyItem


def test_metrics_smoke():
    items = [
        SurveyItem(id="1", question="Don’t you agree that X is good?", known_errors=["leading_question"]),
        SurveyItem(id="2", question="How satisfied or dissatisfied are you with your job?", response_options=["Very dissatisfied", "Somewhat dissatisfied", "Neither satisfied nor dissatisfied", "Somewhat satisfied", "Very satisfied"], known_errors=[]),
    ]
    pipe = ItemReviserPipeline()
    results = [pipe.run(item) for item in items]
    metrics = compute_detection_metrics(items, results)
    assert metrics["num_items"] == 2
    assert "precision" in metrics
