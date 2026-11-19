"""Contracts for the router-control condition (shared detection prompts)."""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest
from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf

from item_reviser.agents.orchestration import ROUTER_OUTPUT_SCHEMA
from item_reviser.constants import ERROR_CATEGORIES
from item_reviser.models.base import _validate_schema
from item_reviser.orchestration.config import DEFAULT_SPECIALIST_FAMILIES
from item_reviser.prompting import AgentPromptConfig, validate_prompt_pipeline_compatibility
from item_reviser.schemas import REPAIR_FAMILIES, ROUTER_DECISIONS

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_shared_router_prompts as builder  # noqa: E402
from final_26_manifest import load_manifest  # noqa: E402
from run_router_control import (  # noqa: E402
    control_overrides,
    load_control_manifest,
    validate_control_manifest,
)

PROMPTS = REPO_ROOT / "prompts" / "agents"
PACKS = (
    ("baseline_codebook", "orchestration_codebook", "orchestration_shared_codebook"),
    ("baseline_p1", "orchestration_p1", "orchestration_shared_p1"),
    ("baseline_p2", "orchestration_p2", "orchestration_shared_p2"),
)
VERBATIM_SECTIONS = (
    "Independent-label test:",
    "Taxonomy definitions and decision boundaries:",
    "Important pairwise boundaries:",
    "Operational response-option and questionnaire-format procedure:",
)
EXAMPLE_RE = re.compile(r"<!-- P2_EXAMPLE_START -->(.*?)<!-- P2_EXAMPLE_END -->", re.S)
INPUT_RE = re.compile(r"Input JSON:\n```json\n(.*?)\n```", re.S)
OUTPUT_RE = re.compile(r"Output JSON:\n```json\n(.*?)\n```", re.S)


def _text(pack: str, role: str) -> str:
    return (PROMPTS / pack / f"{role}.md").read_text(encoding="utf-8")


def _render_context() -> dict:
    return {
        "allowed_categories": ERROR_CATEGORIES,
        "allowed_routes": sorted(ROUTER_DECISIONS),
        "repair_families": sorted(REPAIR_FAMILIES),
        "confidence_threshold": 0.7,
        "output_schema": ROUTER_OUTPUT_SCHEMA,
        "question": "How many workshops did you attend?",
        "response_options": ["None", "One or more"],
    }


def test_generated_router_prompts_are_up_to_date():
    for path, text in builder.expected_outputs().items():
        assert path.read_text(encoding="utf-8") == text, f"regenerate {path}"


@pytest.mark.parametrize(("checker_pack", "_original", "shared_pack"), PACKS)
def test_shared_router_copies_checker_detection_text(checker_pack, _original, shared_pack):
    checker = builder.checker_sections(_text(checker_pack, "quality_checker"))
    router = _text(shared_pack, "router")
    for header in VERBATIM_SECTIONS:
        if header in checker:
            assert checker[header] in router, f"{header} not copied verbatim"
    # Only the documented format substitutions may differ in the remaining sections.
    for header in ("Evidence gate and clean-item rule:", "Output discipline:"):
        section = checker[header]
        for old, new in builder.CHECKER_SUBSTITUTIONS:
            section = section.replace(old, new)
        assert section in router
    assert "severity" not in router
    assert '"errors"' not in router and "`errors`" not in router
    assert "route one clear supported defect" not in router
    assert "Identify every independently supported questionnaire-design problem" in router


@pytest.mark.parametrize(("_checker", "_original", "shared_pack"), PACKS)
def test_shared_router_defines_every_label_in_full(_checker, _original, shared_pack):
    router = _text(shared_pack, "router")
    definitions = router.split("Taxonomy definitions and decision boundaries:\n", 1)[1]
    definitions = definitions.split("\n\n", 1)[0]
    defined = re.findall(r"^- `([a-z_]+)`:", definitions, re.M)
    assert defined == list(ERROR_CATEGORIES)


@pytest.mark.parametrize(("_checker", "_original", "shared_pack"), PACKS)
def test_shared_router_renders_with_router_context(_checker, _original, shared_pack):
    config = AgentPromptConfig(template_path=str(PROMPTS / shared_pack / "router.md"))
    rendered = config.render(_render_context())
    assert "${" not in rendered
    assert "How many workshops did you attend?" in rendered


def test_shared_p2_examples_reuse_checker_items_and_labels():
    checker_blocks = EXAMPLE_RE.findall(_text("baseline_p2", "quality_checker"))
    router_blocks = EXAMPLE_RE.findall(_text("orchestration_shared_p2", "router"))
    assert len(checker_blocks) == len(router_blocks) == 4
    for checker_block, router_block in zip(checker_blocks, router_blocks, strict=True):
        assert INPUT_RE.findall(checker_block) == INPUT_RE.findall(router_block)
        checker_out = json.loads(OUTPUT_RE.search(checker_block).group(1))
        router_out = json.loads(OUTPUT_RE.search(router_block).group(1))
        _validate_schema(router_out, ROUTER_OUTPUT_SCHEMA)
        labels = router_out["taxonomy_labels"]
        assert labels == [error["category"] for error in checker_out["errors"]]
        if not labels:
            assert (router_out["decision"], router_out["recommended_route"]) == ("accept", "accept")
        elif len(labels) == 1:
            assert router_out["decision"] == "revise"
            assert router_out["recommended_route"] == DEFAULT_SPECIALIST_FAMILIES[labels[0]]
        else:
            assert (router_out["decision"], router_out["recommended_route"]) == ("fallback", "fallback")


@pytest.mark.parametrize(("_checker", "original_pack", "shared_pack"), PACKS)
def test_shared_prompt_config_changes_only_the_router(_checker, original_pack, shared_pack):
    GlobalHydra.instance().clear()
    try:
        with initialize_config_dir(config_dir=str(REPO_ROOT / "configs"), version_base=None):
            def prompt_cfg(pack: str) -> dict:
                cfg = compose(
                    config_name="config",
                    overrides=[f"prompt={pack}", "orchestration.enabled=true", f"paths.root={REPO_ROOT}"],
                )
                return OmegaConf.to_container(cfg.prompt, resolve=True)

            original = prompt_cfg(original_pack)
            shared = prompt_cfg(shared_pack)
    finally:
        GlobalHydra.instance().clear()
    assert shared.pop("name") == shared_pack
    assert original.pop("name") == original_pack
    assert Path(shared.pop("router")["template_path"]) == PROMPTS / shared_pack / "router.md"
    assert Path(original.pop("router")["template_path"]) == PROMPTS / original_pack / "router.md"
    assert shared == original


def test_shared_packs_are_rejected_on_the_baseline_pipeline():
    for _checker, _original, shared_pack in PACKS:
        with pytest.raises(ValueError, match="orchestration-only"):
            validate_prompt_pipeline_compatibility({"name": shared_pack}, orchestration_enabled=False)


def test_control_manifest_is_valid_and_matches_august_rows():
    rows = load_control_manifest()
    assert validate_control_manifest(rows, load_manifest()) == []
    kinds = sorted((row["control_kind"], row["pipeline"]) for row in rows)
    assert kinds == [("repro", "baseline")] + [("shared", "orchestrated")] * 5


def test_control_manifest_validation_rejects_drift():
    final_rows = load_manifest()
    rows = load_control_manifest()
    drifted = copy.deepcopy(rows)
    drifted[0]["decoding"]["max_new_tokens"] = 4096
    assert any("decoding differs" in e for e in validate_control_manifest(drifted, final_rows))
    wrong_prompt = copy.deepcopy(rows)
    wrong_prompt[0]["prompt_config"] = "orchestration_codebook"
    assert any("prompt_config must be" in e for e in validate_control_manifest(wrong_prompt, final_rows))


def test_control_overrides_compose_with_hydra():
    GlobalHydra.instance().clear()
    try:
        with initialize_config_dir(config_dir=str(REPO_ROOT / "configs"), version_base=None):
            for row in load_control_manifest():
                overrides = [
                    o for o in control_overrides(row, git_commit="test")
                    if "${oc.env:" not in o and not o.startswith("hydra.")
                ]
                cfg = compose(config_name="config", overrides=[*overrides, f"paths.root={REPO_ROOT}"])
                assert cfg.prompt.name == row["prompt_config"]
                assert cfg.experiment.run_id == row["run_id"]
                assert cfg.orchestration.enabled == row["orchestration_enabled"]
                assert cfg.model.decoding.max_new_tokens == row["decoding"]["max_new_tokens"]
    finally:
        GlobalHydra.instance().clear()
