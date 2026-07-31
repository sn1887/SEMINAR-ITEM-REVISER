from item_reviser.evaluation.metrics import compute_detection_metrics
from item_reviser.evaluation.report import write_markdown_report
from item_reviser.schemas import (
    CheckResult,
    PipelineError,
    PipelineResult,
    RevisedItem,
    SurveyItem,
)


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
    assert metrics["metric_roles"]["primary_detection"] == [
        "precision",
        "recall",
        "f1",
        "exact_match",
        "false_positive_rate_on_clean_items",
        "overcorrection_rate",
    ]
    assert "revision_quality" not in metrics


def test_failed_clean_result_does_not_receive_exact_match_credit():
    item = SurveyItem(
        id="clean",
        question="How satisfied are you?",
        response_options=["Satisfied", "Dissatisfied"],
        known_errors=[],
        expected_revision={
            "question": "How satisfied are you?",
            "response_options": ["Satisfied", "Dissatisfied"],
        },
    )
    result = PipelineResult(
        item_id=item.id,
        original_item=item,
        detected_errors=[],
        revised_item=RevisedItem(
            question=item.question,
            response_options=item.response_options,
            changed=False,
        ),
        error=PipelineError(
            error_type="LLMOutputParseError",
            message="Invalid JSON",
        ),
    )

    metrics = compute_detection_metrics([item], [result])

    assert metrics["exact_match"] == 0


def _revision_quality_fixture() -> dict[str, object]:
    return {
        "scope": "gold_flawed_items_with_valid_expected_questions",
        "eligible_items": 2,
        "scored_items": 2,
        "failed_items": 0,
        "coverage": 1.0,
        "failure_rate": 0.0,
        "question_bertscore_f1": {"value": 0.8, "eligible_items": 2, "scored_items": 2},
        "sari": {"value": 73.0, "eligible_items": 2, "scored_items": 2},
        "exact_question_match_rate": 0,
        "exact_option_match_rate": 0,
        "exact_revision_rate": 0,
        "revision_changed_rate": 1,
    }


def test_report_separates_primary_detection_from_semantic_revision_metrics(tmp_path):
    path = tmp_path / "report.md"
    write_markdown_report(
        path,
        {
            "num_items": 1,
            "successful_items": 1,
            "failed_items": 0,
            "failure_rate": 0,
            "precision": 1,
            "recall": 1,
            "f1": 1,
            "exact_match": 1,
            "false_positive_rate_on_clean_items": 0,
            "overcorrection_rate": 0,
            "revision_quality": _revision_quality_fixture(),
        },
    )

    text = path.read_text(encoding="utf-8")
    assert text.index("## Primary Detection Metrics") < text.index(
        "## Semantic Revision Metrics"
    )
    assert "Question BERTScore F1" in text
    assert "under-credit valid alternative option wording" in text
    assert "Mean question similarity" not in text


def test_oracle_revision_report_does_not_present_detection_as_primary(tmp_path):
    path = tmp_path / "oracle_report.md"
    write_markdown_report(
        path,
        {
            "num_items": 1,
            "successful_items": 1,
            "failed_items": 0,
            "failure_rate": 0,
            "evaluation_mode": "oracle_revision",
            "precision": None,
            "recall": None,
            "f1": None,
            "exact_match": None,
            "metric_applicability": {
                "detection": {"status": "oracle_supplied"},
                "revision_semantic": {"status": "applicable"},
            },
            "revision_quality": _revision_quality_fixture(),
        },
    )

    text = path.read_text(encoding="utf-8")
    assert text.index("## Semantic Revision Metrics") < text.index("## Detection Metrics")
    assert "Not applicable as model-detection performance" in text
    assert "## Primary Detection Metrics" not in text


def test_detection_only_report_suppresses_semantic_revision_numbers(tmp_path):
    path = tmp_path / "detection_only_report.md"
    write_markdown_report(
        path,
        {
            "num_items": 1,
            "successful_items": 1,
            "failed_items": 0,
            "failure_rate": 0,
            "evaluation_mode": "detection_only",
            "precision": 1,
            "recall": 1,
            "f1": 1,
            "exact_match": 1,
            "false_positive_rate_on_clean_items": 0,
            "overcorrection_rate": None,
            "metric_applicability": {
                "detection": {"status": "applicable"},
                "revision_semantic": {
                    "status": "not_applicable",
                    "reason": "The reviser is not run in detection_only mode.",
                },
                "overcorrection": {
                    "status": "not_applicable",
                    "reason": "Forced unchanged.",
                },
            },
            "revision_quality": {
                "metric_role": "not_applicable",
                "applicability": "not_applicable",
                "reason": "The reviser is not run in detection_only mode.",
            },
        },
    )

    text = path.read_text(encoding="utf-8")
    assert "Question BERTScore F1" not in text
    assert "Not applicable: The reviser is not run in detection_only mode." in text


def test_report_notes_orchestration_does_not_predict_severity(tmp_path):
    path = tmp_path / "orchestration_report.md"
    write_markdown_report(
        path,
        {
            "num_items": 1,
            "successful_items": 1,
            "failed_items": 0,
            "failure_rate": 0,
            "precision": 1,
            "recall": 1,
            "f1": 1,
            "exact_match": 1,
            "false_positive_rate_on_clean_items": 0,
            "revision_quality": {},
            "severity": {"orchestration_router_output": "not_predicted"},
        },
    )

    text = path.read_text(encoding="utf-8")
    assert "router does not predict severity" in text
    assert "synthetic compatibility metadata" in text
