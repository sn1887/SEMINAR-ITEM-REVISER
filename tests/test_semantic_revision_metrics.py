from __future__ import annotations

import pytest

from item_reviser.evaluation.metrics import (
    MetricConfig,
    SemanticRevisionMetrics,
    metric_config_from_mapping,
)
from item_reviser.schemas import PipelineError, PipelineResult, RevisedItem, SurveyItem


class FakeBERTScorer:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.calls: list[tuple[list[str], list[str], int | None]] = []

    def score(self, candidates, references, *, batch_size=None):
        self.calls.append((list(candidates), list(references), batch_size))
        scores = self.scores[: len(candidates)]
        return scores, scores, scores


class FakeSARI:
    def __init__(self, value: float = 50.0) -> None:
        self.value = value
        self.calls: list[dict[str, list[str] | list[list[str]]]] = []

    def compute(self, *, sources, predictions, references):
        self.calls.append(
            {"sources": sources, "predictions": predictions, "references": references}
        )
        return {"sari": self.value}


def _result(item: SurveyItem, *, failed: bool = False) -> PipelineResult:
    return PipelineResult(
        item_id=item.id,
        original_item=item,
        detected_errors=[],
        revised_item=RevisedItem(
            question="How satisfied are you with the service?",
            response_options=["Dissatisfied", "Satisfied"],
            changed=True,
        ),
        error=(
            PipelineError(error_type="ModelError", message="failed")
            if failed
            else None
        ),
    )


def test_metric_config_accepts_short_hydra_aliases():
    config = metric_config_from_mapping({"model_type": "local/model", "num_layers": 3, "lang": "en"})

    assert config == MetricConfig(bertscore_model_type="local/model", bertscore_num_layers=3)


def test_metric_config_parses_hydra_boolean_strings_strictly():
    assert metric_config_from_mapping({"offline": "false"}).offline is False
    assert metric_config_from_mapping({"offline": "true"}).offline is True
    assert metric_config_from_mapping({"rescale_with_baseline": "false"}).rescale_with_baseline is False

    with pytest.raises(ValueError, match="offline"):
        metric_config_from_mapping({"offline": "0"})

    with pytest.raises(ValueError, match="rescale_with_baseline"):
        metric_config_from_mapping({"rescale_with_baseline": "maybe"})


def test_metric_metadata_contains_bertscore_hash_and_metric_library_versions():
    suite = SemanticRevisionMetrics(MetricConfig(), bert_scorer=FakeBERTScorer([]), sari_backend=FakeSARI())

    metadata = suite.metadata()

    assert metadata["bertscore_hash"].startswith("distilroberta-base_L5_no-idf")
    assert metadata["package_versions"]["torch"] != "not-installed"
    assert metadata["package_versions"]["transformers"] != "not-installed"
    assert metadata["package_versions"]["bert-score"] == "0.3.13"
    assert set(metadata) == {"metric_config", "package_versions", "bertscore_hash"}


def test_semantic_metrics_exclude_clean_controls_and_report_coverage():
    flawed = SurveyItem(
        id="flawed",
        question="Do you agree the service is excellent?",
        known_errors=["leading_question"],
        expected_revision={
            "question": "How satisfied are you with the service?",
            "response_options": ["Dissatisfied", "Satisfied"],
        },
    )
    failed = SurveyItem(
        id="failed",
        question="Do you agree the service is excellent?",
        known_errors=["leading_question"],
        expected_revision={
            "question": "How satisfied are you with the service?",
            "response_options": ["Dissatisfied", "Satisfied"],
        },
    )
    clean = SurveyItem(
        id="clean",
        question="How satisfied are you with the service?",
        expected_revision={
            "question": "How satisfied are you with the service?",
            "response_options": ["Dissatisfied", "Satisfied"],
        },
    )
    scorer = FakeBERTScorer([1.0] * 5)
    sari = FakeSARI(73.0)
    suite = SemanticRevisionMetrics(MetricConfig(), bert_scorer=scorer, sari_backend=sari)

    revision = suite.score([flawed, failed, clean], [_result(flawed), _result(failed, failed=True), _result(clean)])

    assert revision["excluded_clean_items"] == 1
    assert revision["eligible_items"] == 2
    assert revision["scored_items"] == 1
    assert revision["failed_items"] == 1
    assert revision["failure_rate"] == pytest.approx(0.5)
    assert revision["question_bertscore_f1"]["value"] == 1.0
    assert revision["sari"]["value"] == 73.0
    assert revision["exact_option_match_rate"] == 1.0
    assert sari.calls == [
        {
            "sources": ["Do you agree the service is excellent?"],
            "predictions": ["How satisfied are you with the service?"],
            "references": [["How satisfied are you with the service?"]],
        }
    ]


def test_evaluate_sari_adapter_matches_a_canonical_example():
    suite = SemanticRevisionMetrics(MetricConfig(cache_path=".metric-cache"))
    sari = suite._ensure_sari_backend()

    result = sari.compute(
        sources=["The dog is running quickly."],
        predictions=["The dog runs."],
        references=[["The dog runs quickly."]],
    )

    assert result["sari"] == pytest.approx(73.67063492063491)
