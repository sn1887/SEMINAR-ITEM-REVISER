from __future__ import annotations

import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf

from item_reviser.evaluation.metrics import metric_config_from_mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from final_26_manifest import (  # noqa: E402
    BLOCK_COUNTS,
    REFERENCE_DECODING,
    hydra_overrides,
    load_manifest,
    selected_rows,
    validate_manifest,
)


def test_final_26_manifest_is_complete_unique_and_staticly_valid():
    rows = load_manifest()

    assert validate_manifest(rows) == []
    assert len(rows) == 26
    assert Counter(row["block"] for row in rows) == BLOCK_COUNTS
    assert len({row["run_id"] for row in rows}) == 26


def test_final_26_manifest_has_exact_ablation_structure():
    rows = load_manifest()

    assert all(row["evaluation_mode"] != "detection_only" for row in rows)
    assert all(row["data_config"] == "final_gold_200_v4" for row in rows)
    assert all(row["dataset_version"] == "v4" for row in rows)
    assert all(row["decoding"] == REFERENCE_DECODING for row in rows)
    assert all(bool(row["thinking"]) == (row["block"] == "D") for row in rows)
    assert {row["model_slug"] for row in selected_rows(rows, {"A"})} == {
        "mistral7b_v03",
        "gemma2_9b",
        "qwen35_9b",
    }
    assert {row["model_slug"] for row in selected_rows(rows, {"B", "C", "D"})} == {
        "qwen35_9b"
    }
    assert all(
        row["model_slug"] == "gemma2_9b" and row["evaluation_mode"] == "end_to_end"
        for row in selected_rows(rows, {"E"})
    )


def test_hydra_overrides_log_matrix_metadata_and_keep_gold_blinded():
    row = next(row for row in load_manifest() if row["run_id"] == "d_p2_qwen35_9b_baseline_end_to_end_thinking")

    overrides = hydra_overrides(row, git_commit="deadbeef")

    assert "experiment=final_26_run_matrix" in overrides
    assert "data=final_gold_200_v4" in overrides
    assert "prompt=baseline_p2" in overrides
    assert "model.chat_template.enable_thinking=true" in overrides
    assert "evaluator.include_gold=false" in overrides
    assert "evaluator.metric_config.cache_path=${oc.env:METRIC_CACHE_PATH,.metric-cache}" in overrides
    assert "experiment.git_commit=deadbeef" in overrides
    assert all("known_errors" not in override and "expected_revision" not in override for override in overrides)


def test_manifest_validation_rejects_a_missing_ablation_condition():
    rows = deepcopy(load_manifest())
    rows[0]["evaluation_mode"] = "oracle_revision"

    errors = validate_manifest(rows, check_files=False)

    assert any("do not exactly match" in error for error in errors)


def _compose_final_metric_config(metric_offline: str, monkeypatch: pytest.MonkeyPatch):
    row = next(row for row in load_manifest() if row["run_id"] == "b_p1_qwen35_9b_baseline_end_to_end")
    monkeypatch.setenv("METRIC_OFFLINE", metric_offline)
    monkeypatch.setenv("METRIC_CACHE_PATH", ".metric-cache")
    monkeypatch.setenv("RUN_NAME", "preflight")
    monkeypatch.setenv("HYDRA_OUTPUT_DIR", "outputs/preflight")
    GlobalHydra.instance().clear()
    try:
        with initialize_config_dir(config_dir=str(REPO_ROOT / "configs"), version_base=None):
            cfg = compose(
                config_name="config",
                overrides=hydra_overrides(row, git_commit="preflight"),
            )
        return OmegaConf.to_container(cfg.evaluator.metric_config, resolve=True)
    finally:
        GlobalHydra.instance().clear()


def test_metric_offline_env_interpolation_is_strict_boolean(monkeypatch):
    false_config = metric_config_from_mapping(
        _compose_final_metric_config("false", monkeypatch)
    )
    true_config = metric_config_from_mapping(
        _compose_final_metric_config("true", monkeypatch)
    )

    assert false_config.offline is False
    assert true_config.offline is True

    with pytest.raises(ValueError, match="offline"):
        metric_config_from_mapping(_compose_final_metric_config("definitely", monkeypatch))
