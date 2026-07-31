import json

import pytest

from item_reviser.evaluation.dataset import load_eval_dataset_with_metadata
from item_reviser.evaluation.runner import run_evaluation
from item_reviser.models.base import BaseLLM

PROMPT_CONFIG = {
    "quality_checker": {
        "template": "Check: ${question}",
        "max_retries": 1,
        "timeout_seconds": 10,
    },
    "item_reviser": {
        "template": "Revise: ${question}\nDetected: ${detected_categories}",
        "max_retries": 1,
        "timeout_seconds": 10,
    },
}


class QueueLLM(BaseLLM):
    backend_name = "queue"

    def __init__(self, responses: list[dict[str, object] | str]) -> None:
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
        _ = prompt, timeout_seconds, kwargs
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, str):
            return response
        return json.dumps(response)


def _row(index: int) -> dict[str, object]:
    question = f"How satisfied are you with service {index}?"
    options = [
        "Very dissatisfied",
        "Somewhat dissatisfied",
        "Neither satisfied nor dissatisfied",
        "Somewhat satisfied",
        "Very satisfied",
    ]
    return {
        "id": f"clean-{index}",
        "question": question,
        "response_options": options,
        "known_errors": [],
        "is_flawed": False,
        "expected_revision": {
            "question": question,
            "response_options": options,
            "revision_notes": ["No revision expected."],
        },
        "metadata": {"needs_manual_review": False},
    }


def _label_bearing_row(index: int, *, flawed: bool) -> dict[str, object]:
    row = _row(index)
    if flawed:
        row["id"] = f"candidate-v1-single-leading-question-{index:03d}"
        row["known_errors"] = ["leading_question"]
        row["is_flawed"] = True
        row["question"] = f"Don't you agree that service {index} is excellent?"
    else:
        row["id"] = f"candidate-v1-clean-{index:04d}"
    row["target_concept"] = "LEAK_TARGET_CONCEPT"
    row["topic"] = "LEAK_TOPIC"
    row["metadata"] = {"needs_manual_review": False, "review_notes": "LEAK_REVIEW"}
    return row


def _flawed_row(index: int) -> dict[str, object]:
    row = _row(index)
    row["known_errors"] = ["leading_question"]
    row["is_flawed"] = True
    row["question"] = f"Don't you agree that service {index} is excellent?"
    row["expected_revision"] = {
        "question": f"How would you rate service {index}?",
        "response_options": row["response_options"],
        "revision_notes": ["Remove leading wording."],
    }
    return row


def test_run_evaluation_reports_progress_metrics(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(
        "\n".join(json.dumps(_row(index)) for index in range(1, 4)),
        encoding="utf-8",
    )
    model = QueueLLM([{"errors": []}, {"errors": []}, {"errors": []}])
    progress_calls: list[tuple[int, int, dict[str, object]]] = []

    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=tmp_path / "outputs",
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=False,
        write_report=False,
        progress_callback=lambda completed, total, partial: progress_calls.append(
            (completed, total, partial)
        ),
        progress_interval=2,
    )

    assert metrics["num_items"] == 3
    assert [completed for completed, _, _ in progress_calls] == [2, 3]
    assert [total for _, total, _ in progress_calls] == [3, 3]
    assert progress_calls[0][2]["num_items"] == 2
    assert progress_calls[0][2]["progress"]["completed_items"] == 2
    assert progress_calls[1][2]["num_items"] == 3
    assert progress_calls[1][2]["progress"]["fraction"] == 1.0


def test_end_to_end_mode_preserves_checker_then_reviser_behavior(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(json.dumps(_flawed_row(1)), encoding="utf-8")
    model = QueueLLM(
        [
            {
                "errors": [
                    {
                        "category": "leading_question",
                        "severity": "high",
                        "explanation": "The question cues agreement.",
                    }
                ]
            },
            {
                "question": "How would you rate service 1?",
                "response_options": _row(1)["response_options"],
                "revision_notes": ["Removed leading wording."],
                "changed": True,
            },
        ]
    )

    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=tmp_path / "outputs",
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=False,
        write_report=False,
        evaluation_mode="end_to_end",
    )

    assert metrics["evaluation_mode"] == "end_to_end"
    assert metrics["evaluator"]["mode"] == "end_to_end"
    assert len(model.prompts) == 2
    assert "Check:" in model.prompts[0]
    assert "Revise:" in model.prompts[1]


def test_detection_only_mode_skips_reviser_and_reports_detection(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(json.dumps(_flawed_row(1)), encoding="utf-8")
    model = QueueLLM(
        [
            {
                "errors": [
                    {
                        "category": "leading_question",
                        "severity": "high",
                        "explanation": "The question cues agreement.",
                    }
                ]
            }
        ]
    )
    output_dir = tmp_path / "outputs"

    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=output_dir,
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=True,
        write_report=False,
        write_predictions_incrementally=False,
        evaluation_mode="detection_only",
    )

    row = json.loads((output_dir / "predictions.jsonl").read_text(encoding="utf-8"))
    assert metrics["evaluation_mode"] == "detection_only"
    assert metrics["precision"] == 1
    assert metrics["overcorrection_rate"] is None
    assert metrics["revision_quality"]["applicability"] == "not_applicable"
    assert metrics["metric_applicability"]["revision_semantic"]["status"] == "not_applicable"
    assert row["predicted_categories"] == ["leading_question"]
    assert row["revised_item"]["question"] == _flawed_row(1)["question"]
    assert row["revised_item"]["changed"] is False
    assert len(model.prompts) == 1
    assert "Check:" in model.prompts[0]


def test_oracle_revision_mode_uses_gold_labels_and_skips_checker(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(json.dumps(_flawed_row(1)), encoding="utf-8")
    model = QueueLLM(
        [
            {
                "question": "How would you rate service 1?",
                "response_options": _row(1)["response_options"],
                "revision_notes": ["Used gold label to remove leading wording."],
                "changed": True,
            }
        ]
    )
    output_dir = tmp_path / "outputs"

    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=output_dir,
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=True,
        write_report=False,
        write_predictions_incrementally=False,
        evaluation_mode="oracle_revision",
    )

    row = json.loads((output_dir / "predictions.jsonl").read_text(encoding="utf-8"))
    assert metrics["evaluation_mode"] == "oracle_revision"
    assert metrics["precision"] is None
    assert metrics["recall"] is None
    assert metrics["oracle_supplied_detection_metrics"]["precision"] == 1
    assert metrics["metric_applicability"]["detection"]["status"] == "oracle_supplied"
    assert metrics["revision_quality"]["applicability"] == "not_applicable"
    assert row["predicted_categories"] == ["leading_question"]
    assert row["detected_errors"][0]["checker"] == "gold_oracle"
    assert row["revised_item"]["changed"] is True
    assert len(model.prompts) == 1
    assert "Revise:" in model.prompts[0]
    assert "leading_question" in model.prompts[0]


def test_oracle_revision_mode_leaves_clean_items_unchanged_without_llm_call(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(json.dumps(_row(1)), encoding="utf-8")
    model = QueueLLM([])
    output_dir = tmp_path / "outputs"

    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=output_dir,
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=True,
        write_report=False,
        write_predictions_incrementally=False,
        evaluation_mode="oracle_revision",
    )

    row = json.loads((output_dir / "predictions.jsonl").read_text(encoding="utf-8"))
    assert metrics["evaluation_mode"] == "oracle_revision"
    assert metrics["revision_quality"]["applicability"] == "not_applicable"
    assert metrics["metric_applicability"]["revision_semantic"]["status"] == "not_applicable"
    assert row["predicted_categories"] == []
    assert row["revised_item"]["question"] == _row(1)["question"]
    assert row["revised_item"]["changed"] is False
    assert model.prompts == []


def test_run_evaluation_rejects_unknown_evaluation_mode(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(json.dumps(_row(1)), encoding="utf-8")

    with pytest.raises(ValueError, match="evaluator.mode"):
        run_evaluation(
            data_path=dataset_path,
            output_dir=tmp_path / "outputs",
            model=QueueLLM([]),
            prompt_config=PROMPT_CONFIG,
            write_predictions=False,
            write_report=False,
            evaluation_mode="unknown",
        )


def test_semantic_metrics_preflight_once_and_score_only_after_final_item(tmp_path, monkeypatch):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(json.dumps(_flawed_row(1)), encoding="utf-8")
    instances = []

    class FakeSemanticMetrics:
        def __init__(self, config):
            self.config = config
            self.preflight_calls = 0
            self.score_calls = 0
            instances.append(self)

        def preflight(self):
            self.preflight_calls += 1
            return {}

        def score(self, items, results):
            self.score_calls += 1
            return {
                "metric_role": "supporting_revision_metrics",
                "scope": "gold_flawed_items_with_valid_expected_questions",
                "eligible_items": len(items),
                "scored_items": len(results),
                "failed_items": 0,
                "coverage": 1.0,
                "failure_rate": 0.0,
                "question_bertscore_f1": {"value": 1.0},
                "sari": {"value": 100.0},
                "metric_config": self.config.to_dict(),
                "package_versions": {},
            }

    monkeypatch.setattr(
        "item_reviser.evaluation.runner.SemanticRevisionMetrics", FakeSemanticMetrics
    )
    progress = []
    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=tmp_path / "outputs",
        model=QueueLLM(
            [
                {"errors": [{"category": "leading_question", "severity": "high", "explanation": "Leading."}]},
                {
                    "question": "How would you rate service 1?",
                    "response_options": _row(1)["response_options"],
                    "revision_notes": ["Neutral."],
                    "changed": True,
                },
            ]
        ),
        prompt_config=PROMPT_CONFIG,
        write_predictions=False,
        write_report=False,
        progress_callback=lambda _completed, _total, partial: progress.append(partial),
        progress_interval=1,
        revision_metric_config={"cache_path": str(tmp_path / "metric-cache")},
    )

    assert instances[0].preflight_calls == 1
    assert instances[0].score_calls == 1
    assert progress[0]["revision_quality"]["applicability"] == "pending"
    assert metrics["revision_quality"]["question_bertscore_f1"]["value"] == 1.0


def test_run_evaluation_records_item_failure_and_continues(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(
        "\n".join(
            [
                json.dumps(_row(1)),
                json.dumps(_flawed_row(2)),
                json.dumps(_row(3)),
            ]
        ),
        encoding="utf-8",
    )
    model = QueueLLM(
        [
            {"errors": []},
            "not json",
            {"errors": []},
        ]
    )
    progress_calls: list[tuple[int, int, dict[str, object]]] = []
    output_dir = tmp_path / "outputs"

    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=output_dir,
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=True,
        write_report=True,
        progress_callback=lambda completed, total, partial: progress_calls.append(
            (completed, total, partial)
        ),
        progress_interval=1,
        continue_on_item_error=True,
        write_predictions_incrementally=True,
        include_error_traceback=False,
    )

    prediction_rows = [
        json.loads(line)
        for line in (output_dir / "predictions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert metrics["num_items"] == 3
    assert metrics["failed_items"] == 1
    assert metrics["successful_items"] == 2
    assert metrics["failures"]["types"]["LLMOutputParseError"] == 1
    assert metrics["false_negatives"] == 1
    assert [completed for completed, _, _ in progress_calls] == [1, 2, 3]
    assert progress_calls[1][2]["failed_items"] == 1
    assert len(prediction_rows) == 3
    assert prediction_rows[1]["item_id"] == "eval-000002"
    assert prediction_rows[1]["error"]["error_type"] == "LLMOutputParseError"
    assert prediction_rows[1]["revised_item"]["changed"] is False
    assert prediction_rows[1]["original_item"] == {
        "question": "Don't you agree that service 2 is excellent?",
        "response_options": _row(2)["response_options"],
    }
    assert "known_errors" not in prediction_rows[1]["original_item"]
    assert "expected_revision" not in prediction_rows[1]["original_item"]
    assert "metadata" not in prediction_rows[1]["original_item"]
    assert metrics["failures"]["items"][0]["item_id"] == "eval-000002"
    assert metrics["artifacts"]["gold_in_prediction_rows"] is False
    assert "LLMOutputParseError" in (output_dir / "report.md").read_text(
        encoding="utf-8"
    )


def test_run_evaluation_blinds_label_bearing_source_ids_and_gold_fields(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(
        "\n".join(
            [
                json.dumps(_label_bearing_row(1, flawed=False)),
                json.dumps(_label_bearing_row(2, flawed=True)),
            ]
        ),
        encoding="utf-8",
    )
    model = QueueLLM([{"errors": []}, {"errors": []}])
    output_dir = tmp_path / "outputs"

    run_evaluation(
        data_path=dataset_path,
        output_dir=output_dir,
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=True,
        write_report=False,
        write_predictions_incrementally=False,
    )

    predictions_text = (output_dir / "predictions.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in predictions_text.splitlines()]

    assert [row["item_id"] for row in rows] == ["eval-000001", "eval-000002"]
    assert "candidate-v1-clean" not in predictions_text
    assert "candidate-v1-single-leading-question" not in predictions_text
    assert "LEAK_TARGET_CONCEPT" not in predictions_text
    assert "LEAK_TOPIC" not in predictions_text
    assert "LEAK_REVIEW" not in predictions_text
    for row in rows:
        assert set(row["original_item"]) == {"question", "response_options"}


def test_run_evaluation_include_gold_debug_mode_is_explicit(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(
        json.dumps(_label_bearing_row(1, flawed=True)),
        encoding="utf-8",
    )
    model = QueueLLM([{"errors": []}])
    output_dir = tmp_path / "outputs"

    metrics = run_evaluation(
        data_path=dataset_path,
        output_dir=output_dir,
        model=model,
        prompt_config=PROMPT_CONFIG,
        write_predictions=True,
        write_report=False,
        write_predictions_incrementally=False,
        include_gold=True,
    )

    row = json.loads((output_dir / "predictions.jsonl").read_text(encoding="utf-8"))
    assert row["item_id"] == "candidate-v1-single-leading-question-001"
    assert row["original_item"]["known_errors"] == ["leading_question"]
    assert metrics["artifacts"]["gold_in_prediction_rows"] is True


def test_max_items_uses_deterministic_stratified_sampling(tmp_path):
    dataset_path = tmp_path / "eval.jsonl"
    rows = [
        *(_label_bearing_row(index, flawed=False) for index in range(1, 5)),
        *(_label_bearing_row(index, flawed=True) for index in range(5, 11)),
    ]
    dataset_path.write_text(
        "\n".join(json.dumps(row) for row in rows),
        encoding="utf-8",
    )

    sampled, metadata = load_eval_dataset_with_metadata(
        dataset_path,
        max_items=5,
        sampling_seed=123,
    )
    sampled_again, metadata_again = load_eval_dataset_with_metadata(
        dataset_path,
        max_items=5,
        sampling_seed=123,
    )
    full, full_metadata = load_eval_dataset_with_metadata(dataset_path)

    assert [item.id for item in sampled] == [item.id for item in sampled_again]
    assert metadata.to_dict() == metadata_again.to_dict()
    assert any(item.known_errors for item in sampled)
    assert any(not item.known_errors for item in sampled)
    assert metadata.requested_max_items == 5
    assert metadata.returned_records == 5
    assert metadata.sampling_method == "deterministic_stratified_by_flaw_status"
    assert metadata.sampling_seed == 123
    assert metadata.sampled_opaque_ids == [
        "eval-000001",
        "eval-000002",
        "eval-000003",
        "eval-000004",
        "eval-000005",
    ]
    assert [item.id for item in full] == [str(row["id"]) for row in rows]
    assert full_metadata.sampling_method == "full_dataset"
