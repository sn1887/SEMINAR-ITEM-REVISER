import json

from item_reviser.evaluation.runner import run_evaluation
from item_reviser.models.base import BaseLLM


PROMPT_CONFIG = {
    "quality_checker": {
        "template": "Check: ${question}",
        "max_retries": 1,
        "timeout_seconds": 10,
    },
    "item_reviser": {
        "template": "Revise: ${question}",
        "max_retries": 1,
        "timeout_seconds": 10,
    },
}


class QueueLLM(BaseLLM):
    backend_name = "queue"

    def __init__(self, responses: list[dict[str, object] | str]) -> None:
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
    assert prediction_rows[1]["item_id"] == "clean-2"
    assert prediction_rows[1]["error"]["error_type"] == "LLMOutputParseError"
    assert prediction_rows[1]["revised_item"]["changed"] is False
    assert "LLMOutputParseError" in (output_dir / "report.md").read_text(
        encoding="utf-8"
    )
