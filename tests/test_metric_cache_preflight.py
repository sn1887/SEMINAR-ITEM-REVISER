from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = REPO_ROOT / "scripts" / "metric_cache_preflight.py"


def _load_preflight_script():
    spec = importlib.util.spec_from_file_location("metric_cache_preflight_script", PREFLIGHT_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_metric_cache_preflight_verifies_connected_then_offline(monkeypatch):
    script = _load_preflight_script()
    calls: list[bool] = []

    class FakeSemanticRevisionMetrics:
        def __init__(self, config) -> None:
            self.config = config
            calls.append(bool(config.offline))

        def preflight(self):
            return {
                "metric_config": self.config.to_dict(),
                "bertscore_hash": "hash",
                "package_versions": {"torch": "test", "transformers": "test"},
            }

        def score(self, items, results):
            return {
                "question_bertscore_f1": {"value": 1.0},
                "sari": {"value": 100.0},
            }

    monkeypatch.setattr(script, "SemanticRevisionMetrics", FakeSemanticRevisionMetrics)

    summary = script.run_metric_cache_preflight(script.MetricConfig(cache_path="cache"))

    assert calls == [False, True]
    assert summary["connected"]["metric_config"]["offline"] is False
    assert summary["offline"]["metric_config"]["offline"] is True
