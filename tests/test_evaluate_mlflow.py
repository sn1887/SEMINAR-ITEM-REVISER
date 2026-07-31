from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
from omegaconf import OmegaConf

REPO_ROOT = Path(__file__).resolve().parents[1]
EVALUATE_SCRIPT = REPO_ROOT / "scripts" / "evaluate.py"


def _load_evaluate_script():
    spec = importlib.util.spec_from_file_location("seminar_evaluate_script", EVALUATE_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeMLflow:
    def __init__(self) -> None:
        self.params: list[dict[str, str]] = []
        self.metrics: list[tuple[dict[str, float], int]] = []
        self.artifacts: list[tuple[str, str]] = []

    def log_params(self, params: dict[str, str]) -> None:
        self.params.append(dict(params))

    def log_metrics(self, metrics: dict[str, float], *, step: int) -> None:
        self.metrics.append((dict(metrics), step))

    def log_artifacts(self, path: str, *, artifact_path: str) -> None:
        self.artifacts.append((path, artifact_path))


def test_mlflow_logs_final_semantic_metrics_after_terminal_pending_progress(tmp_path):
    evaluate_script = _load_evaluate_script()
    mlflow = FakeMLflow()
    final_metrics: dict[str, Any] = {
        "num_items": 2,
        "revision_quality": {
            "question_bertscore_f1": {"value": 0.91},
            "sari": {"value": 77.5},
            "metric_config": {"offline": True},
            "package_versions": {"torch": "2.5.1", "transformers": "5.10.0.dev0"},
            "bertscore_hash": "distilroberta-base_L5_no-idf_version=0.3.13",
        },
    }

    # Regression shape: the progress callback has already logged step=num_items
    # with semantic metrics still pending, so final output logging is called with
    # log_metrics=False to avoid replaying all progress scalars.
    mlflow.log_metrics({"revision_quality.applicability": 0.0}, step=2)
    evaluate_script._log_mlflow_final_outputs(
        mlflow,
        final_metrics,
        tmp_path,
        log_metrics=False,
    )

    assert mlflow.metrics[-1] == (
        {
            "revision_quality.question_bertscore_f1.value": 0.91,
            "revision_quality.sari.value": 77.5,
        },
        2,
    )
    flattened_params = {key: value for params in mlflow.params for key, value in params.items()}
    assert flattened_params["revision_metrics.bertscore_hash"].startswith("distilroberta-base")
    assert flattened_params["revision_metrics.packages.torch"] == "2.5.1"
    assert flattened_params["revision_metrics.packages.transformers"] == "5.10.0.dev0"


def test_evaluate_validates_prompt_pipeline_before_model_construction(monkeypatch):
    evaluate_script = _load_evaluate_script()
    build_model_called = False

    def fail_build_model(_cfg: object) -> object:
        nonlocal build_model_called
        build_model_called = True
        raise AssertionError("build_model should not run for prompt/pipeline mismatch")

    monkeypatch.setattr(evaluate_script, "build_model", fail_build_model)
    cfg = OmegaConf.create(
        {
            "seed": 7,
            "prompt": {"name": "baseline_p2"},
            "orchestration": {"enabled": True},
        }
    )

    with pytest.raises(ValueError, match="baseline-only"):
        evaluate_script.main.__wrapped__(cfg)

    assert build_model_called is False
