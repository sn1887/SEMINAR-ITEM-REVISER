from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf

from item_reviser.agents.orchestration import (
    ORCHESTRATED_REVISER_OUTPUT_SCHEMA,
    REVISION_PLAN_OUTPUT_SCHEMA,
    ROUTER_OUTPUT_SCHEMA,
    VALIDATOR_OUTPUT_SCHEMA,
    _validator_output_schema,
)
from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.constants import ERROR_CATEGORIES
from item_reviser.models.base import (
    CHECKER_OUTPUT_SCHEMA,
    REVISER_OUTPUT_SCHEMA,
    BaseLLM,
    LLMOutputSchemaError,
    _validate_schema,
)
from item_reviser.orchestration.config import (
    DEFAULT_AGENT_PROMPTS,
    DEFAULT_SPECIALIST_FAMILIES,
    OrchestrationConfig,
)
from item_reviser.prompting import (
    AgentPromptConfig,
    validate_prompt_pipeline_compatibility,
)
from item_reviser.schemas import (
    REPAIR_FAMILIES,
    ROUTER_DECISIONS,
    VALIDATION_STATUSES,
    ValidatorResult,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from final_26_manifest import hydra_overrides, load_manifest  # noqa: E402

P2_ROLE_SCHEMAS = {
    "baseline_p2/quality_checker.md": CHECKER_OUTPUT_SCHEMA,
    "baseline_p2/item_reviser.md": REVISER_OUTPUT_SCHEMA,
    "orchestration_p2/router.md": ROUTER_OUTPUT_SCHEMA,
    "orchestration_p2/fallback_reviser.md": ORCHESTRATED_REVISER_OUTPUT_SCHEMA,
    "orchestration_p2/specialist_wording_clarity.md": (
        ORCHESTRATED_REVISER_OUTPUT_SCHEMA
    ),
    "orchestration_p2/specialist_response_options_scale.md": (
        ORCHESTRATED_REVISER_OUTPUT_SCHEMA
    ),
    "orchestration_p2/specialist_construct_alignment.md": (
        ORCHESTRATED_REVISER_OUTPUT_SCHEMA
    ),
    "orchestration_p2/specialist_bias_sensitivity.md": (
        ORCHESTRATED_REVISER_OUTPUT_SCHEMA
    ),
    "orchestration_p2/specialist_questionnaire_format.md": (
        ORCHESTRATED_REVISER_OUTPUT_SCHEMA
    ),
    "orchestration_p2/validator.md": VALIDATOR_OUTPUT_SCHEMA,
}
BASELINE_ROLES = ("quality_checker", "item_reviser")
ORCHESTRATION_ROLES = tuple(DEFAULT_AGENT_PROMPTS.values())
TREATMENT_PIPELINES = (
    ("baseline_codebook", False, BASELINE_ROLES),
    ("orchestration_codebook", True, ORCHESTRATION_ROLES),
    ("baseline_p1", False, BASELINE_ROLES),
    ("orchestration_p1", True, ORCHESTRATION_ROLES),
    ("baseline_p2", False, BASELINE_ROLES),
    ("orchestration_p2", True, ORCHESTRATION_ROLES),
)
EXAMPLE_RE = re.compile(
    r"<!-- P2_EXAMPLE_START -->(.*?)<!-- P2_EXAMPLE_END -->",
    flags=re.DOTALL,
)
OUTPUT_RE = re.compile(
    r"<!-- P2_OUTPUT_EXAMPLE_START -->(.*?)<!-- P2_OUTPUT_EXAMPLE_END -->",
    flags=re.DOTALL,
)
JSON_FENCE_RE = re.compile(r"```json\s*(.*?)\s*```", flags=re.DOTALL | re.IGNORECASE)
UNRESOLVED_PLACEHOLDER_RE = re.compile(r"\$\{[^}\n]+\}")
CANONICAL_ROUTES = REPAIR_FAMILIES | {"accept"}
CANONICAL_AGENTS = set(DEFAULT_AGENT_PROMPTS.values())
CANONICAL_CHECKERS = {"llm", "llm_router", "gold_oracle"}
ROUTED_ISSUE_PROMPT_SCHEMA = {
    "type": "object",
    "required": ["category", "explanation", "evidence", "suggestion", "checker"],
    "additionalProperties": False,
    "properties": {
        "category": {"type": "string"},
        "explanation": {"type": "string"},
        "evidence": {"type": ["string", "null"]},
        "suggestion": {"type": ["string", "null"]},
        "checker": {"type": "string"},
    },
}
QUESTIONNAIRE_FORMAT_INPUT_SCHEMA = {
    "type": "object",
    "required": [
        "question",
        "response_options",
        "detected_issues",
        "router_decision",
        "revision_plan",
        "retry_instructions",
    ],
    "additionalProperties": False,
    "properties": {
        "question": {"type": "string"},
        "response_options": {"type": "array", "items": {"type": "string"}},
        "detected_issues": {
            "type": "array",
            "items": ROUTED_ISSUE_PROMPT_SCHEMA,
        },
        "router_decision": ROUTER_OUTPUT_SCHEMA,
        "revision_plan": REVISION_PLAN_OUTPUT_SCHEMA,
        "retry_instructions": {"type": "array", "items": {"type": "string"}},
    },
}


class NoopLLM(BaseLLM):
    backend_name = "noop"

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> str:
        _ = prompt, timeout_seconds, kwargs
        raise AssertionError("A compatibility failure must occur before any model call")


def _p2_path(relative_path: str) -> Path:
    return REPO_ROOT / "prompts" / "agents" / relative_path


def _example_blocks(relative_path: str) -> list[str]:
    text = _p2_path(relative_path).read_text(encoding="utf-8")
    starts = text.count("<!-- P2_EXAMPLE_START -->")
    ends = text.count("<!-- P2_EXAMPLE_END -->")
    blocks = EXAMPLE_RE.findall(text)
    assert starts == ends == len(blocks), f"Unbalanced P2 example markers in {relative_path}"
    assert blocks, f"No complete P2 examples in {relative_path}"
    return blocks


def _output_payload(block: str) -> dict[str, Any]:
    output_blocks = OUTPUT_RE.findall(block)
    assert len(output_blocks) == 1, "Each P2 example must contain exactly one nested output block"
    fences = JSON_FENCE_RE.findall(output_blocks[0])
    assert len(fences) == 1, "Each P2 output marker must contain exactly one JSON fence"
    payload = json.loads(fences[0])
    assert isinstance(payload, dict)
    return payload


def _input_payload(block: str) -> dict[str, Any]:
    before_output = block.partition("<!-- P2_OUTPUT_EXAMPLE_START -->")[0]
    fences = JSON_FENCE_RE.findall(before_output)
    assert fences, "Expected a JSON input before the nested P2 output block"
    payload = json.loads(fences[-1])
    assert isinstance(payload, dict)
    return payload


def _walk_json(value: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key, nested
            yield from _walk_json(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_json(nested)


def _assert_canonical_identifier(key: str, value: Any, location: str) -> None:
    if key == "category":
        assert value in ERROR_CATEGORIES, f"Noncanonical taxonomy category in {location}: {value}"
    elif key == "taxonomy_labels":
        assert isinstance(value, list)
        assert set(value) <= set(ERROR_CATEGORIES), (
            f"Noncanonical taxonomy label in {location}: {value}"
        )
    elif key == "decision":
        assert value in ROUTER_DECISIONS, f"Noncanonical router decision in {location}: {value}"
    elif key == "recommended_route":
        assert value in CANONICAL_ROUTES, f"Noncanonical route in {location}: {value}"
    elif key == "repair_family":
        assert value in REPAIR_FAMILIES, f"Noncanonical repair family in {location}: {value}"
    elif key in {"selected_agent", "agent_name"}:
        assert value in CANONICAL_AGENTS, f"Noncanonical agent identifier in {location}: {value}"
    elif key == "checker":
        assert value in CANONICAL_CHECKERS, f"Noncanonical checker identifier in {location}: {value}"
    elif key == "status":
        assert value in VALIDATION_STATUSES, f"Noncanonical status in {location}: {value}"
    elif key == "severity":
        assert value in {"low", "medium", "high"}, (
            f"Noncanonical severity in {location}: {value}"
        )


def _assert_text_identifiers_are_canonical(block: str, location: str) -> None:
    scalar_pattern = re.compile(
        r"(?m)^\s*(?:-\s*)?"
        r"(category|decision|recommended_route|repair_family|selected_agent|status|severity)"
        r":\s*[`\"']?([a-z0-9_-]+)"
    )
    for key, value in scalar_pattern.findall(block):
        _assert_canonical_identifier(key, value, location)

    for raw_labels in re.findall(r"(?m)^\s*taxonomy_labels:\s*\[([^]]*)\]", block):
        labels = [part.strip().strip("`\"'") for part in raw_labels.split(",") if part.strip()]
        _assert_canonical_identifier("taxonomy_labels", labels, location)


def _compose_prompt_pack(prompt_pack: str, orchestration_enabled: bool):
    return compose(
        config_name="config",
        overrides=[
            f"prompt={prompt_pack}",
            f"orchestration.enabled={str(orchestration_enabled).lower()}",
            f"paths.root={REPO_ROOT}",
        ],
    )


def _render_context() -> dict[str, Any]:
    router_decision = {
        "decision": "revise",
        "taxonomy_labels": ["non_exclusive_options"],
        "confidence": 0.95,
        "evidence": "Two ranges overlap.",
        "rationale": "A supported repair is needed.",
        "recommended_route": "response_options_scale",
    }
    revision_plan = {
        "repair_family": "response_options_scale",
        "selected_agent": "response_options_scale",
        "instructions": ["Remove only the overlap."],
        "fallback_reason": None,
        "rationale": "Use the matching specialist.",
    }
    return {
        "allowed_categories": ERROR_CATEGORIES,
        "allowed_routes": sorted(ROUTER_DECISIONS),
        "repair_families": sorted(REPAIR_FAMILIES),
        "confidence_threshold": 0.7,
        "output_schema": {},
        "question": "How many workshops did you attend?",
        "response_options": ["None", "One or more"],
        "detected_categories": ["non_exclusive_options"],
        "detected_issues": [],
        "router_decision": router_decision,
        "fallback_reason": "Representative render context.",
        "retry_instructions": [],
        "retry_count": 0,
        "suggested_repair_family": "response_options_scale",
        "suggested_agent": "response_options_scale",
        "specialist_scope": "Response options and scale structure.",
        "revision_plan": revision_plan,
        "validation_criteria": ["Preserve the construct."],
        "candidate_revision": {
            "question": "How many workshops did you attend?",
            "response_options": ["None", "One or more"],
            "revision_notes": [],
            "changed": False,
        },
        "remaining_retry_budget": 1,
    }


def test_every_nested_p2_output_is_json_and_matches_its_exact_runtime_schema():
    discovered = {
        str(path.relative_to(REPO_ROOT / "prompts" / "agents"))
        for pack in ("baseline_p2", "orchestration_p2")
        for path in (REPO_ROOT / "prompts" / "agents" / pack).glob("*.md")
        if "<!-- P2_EXAMPLE_START -->" in path.read_text(encoding="utf-8")
    }
    assert discovered == set(P2_ROLE_SCHEMAS)

    for relative_path, schema in P2_ROLE_SCHEMAS.items():
        for index, block in enumerate(_example_blocks(relative_path), start=1):
            assert "Input" in block or "input" in block
            payload = _output_payload(block)
            if relative_path == "orchestration_p2/validator.md":
                input_payload = _input_payload(block)
                schema = _validator_output_schema(
                    has_detected_issues=bool(input_payload["detected_issues"])
                )
            _validate_schema(payload, schema)
            if relative_path == "baseline_p2/quality_checker.md":
                for error in payload["errors"]:
                    assert {"category", "severity", "explanation", "evidence"} <= set(error), (
                        f"Incomplete checker error in {relative_path} example {index}"
                    )


def test_p2_example_inventory_matches_the_frozen_experiment_design():
    expected_counts = {
        "baseline_p2/quality_checker.md": 4,
        "baseline_p2/item_reviser.md": 4,
        "orchestration_p2/router.md": 8,
        "orchestration_p2/fallback_reviser.md": 3,
        "orchestration_p2/specialist_wording_clarity.md": 2,
        "orchestration_p2/specialist_response_options_scale.md": 5,
        "orchestration_p2/specialist_construct_alignment.md": 2,
        "orchestration_p2/specialist_bias_sensitivity.md": 2,
        "orchestration_p2/specialist_questionnaire_format.md": 2,
        "orchestration_p2/validator.md": 5,
    }

    actual_counts = {
        relative_path: len(_example_blocks(relative_path))
        for relative_path in expected_counts
    }
    assert actual_counts == expected_counts
    assert sum(actual_counts.values()) == 37


def test_p2_examples_use_only_canonical_runtime_identifiers():
    for relative_path in P2_ROLE_SCHEMAS:
        for index, block in enumerate(_example_blocks(relative_path), start=1):
            location = f"{relative_path} example {index}"
            for fenced_json in JSON_FENCE_RE.findall(block):
                payload = json.loads(fenced_json)
                for key, value in _walk_json(payload):
                    _assert_canonical_identifier(key, value, location)
            _assert_text_identifiers_are_canonical(block, location)


def test_baseline_p2_clean_demo_satisfies_clean_and_option_safeguards():
    checker_examples = [
        (_input_payload(block), _output_payload(block))
        for block in _example_blocks("baseline_p2/quality_checker.md")
    ]
    reviser_examples = [
        (_input_payload(block), _output_payload(block))
        for block in _example_blocks("baseline_p2/item_reviser.md")
    ]
    clean_input, clean_check = next(pair for pair in checker_examples if pair[1] == {"errors": []})
    revise_input, clean_revision = next(
        pair for pair in reviser_examples if pair[0]["detected_categories"] == []
    )

    assert clean_input == {
        "question": "During the past 30 days, did you borrow at least one printed book from a library?",
        "response_options": [
            "Yes, I borrowed at least one printed book",
            "No, I did not borrow a printed book",
        ],
    }
    assert revise_input["question"] == clean_input["question"]
    assert revise_input["response_options"] == clean_input["response_options"]
    assert revise_input["detected_issues"] == []
    assert clean_check["errors"] == []
    assert clean_revision["question"] == clean_input["question"]
    assert clean_revision["response_options"] == clean_input["response_options"]
    assert clean_revision["changed"] is False

    normalized_options = [option.casefold() for option in clean_input["response_options"]]
    assert len(normalized_options) == len(set(normalized_options)) == 2
    assert normalized_options[0].startswith("yes")
    assert normalized_options[1].startswith("no")
    assert "did you borrow" in clean_input["question"].casefold()


def test_open_closed_mismatch_is_mapped_and_hydra_wired_to_format_specialists():
    assert DEFAULT_SPECIALIST_FAMILIES["open_closed_mismatch"] == "questionnaire_format"
    GlobalHydra.instance().clear()
    try:
        with initialize_config_dir(config_dir=str(REPO_ROOT / "configs"), version_base=None):
            for pack in ("orchestration_p1", "orchestration_p2"):
                cfg = _compose_prompt_pack(pack, True)
                runtime = OrchestrationConfig.from_config(cfg.orchestration)
                assert runtime.family_for_label("open_closed_mismatch") == "questionnaire_format"
                path = Path(str(cfg.prompt.questionnaire_format.template_path))
                assert path == (
                    REPO_ROOT
                    / "prompts"
                    / "agents"
                    / pack
                    / "specialist_questionnaire_format.md"
                )
                text = path.read_text(encoding="utf-8")
                assert "open_closed_mismatch" in text
                assert "open response" in text.casefold()
                assert "closed" in text.casefold()
    finally:
        GlobalHydra.instance().clear()


def test_p2_questionnaire_format_demo_inputs_match_runtime_context_contract():
    examples = [
        (_input_payload(block), _output_payload(block))
        for block in _example_blocks("orchestration_p2/specialist_questionnaire_format.md")
    ]

    assert len(examples) == 2
    for input_payload, output_payload in examples:
        _validate_schema(input_payload, QUESTIONNAIRE_FORMAT_INPUT_SCHEMA)
        _validate_schema(output_payload, ORCHESTRATED_REVISER_OUTPUT_SCHEMA)
        assert input_payload["detected_issues"]
        for issue in input_payload["detected_issues"]:
            assert set(issue) == {
                "category",
                "explanation",
                "evidence",
                "suggestion",
                "checker",
            }
            assert issue["category"] == "open_closed_mismatch"
            assert issue["suggestion"] == "questionnaire_format"
            assert issue["checker"] == "llm_router"
            assert "severity" not in issue
        assert input_payload["router_decision"]["recommended_route"] == "questionnaire_format"
        assert input_payload["revision_plan"]["repair_family"] == "questionnaire_format"
        assert input_payload["revision_plan"]["selected_agent"] == "questionnaire_format"
        assert input_payload["retry_instructions"] == []


def test_p2_fallback_examples_cover_representative_fallback_conditions():
    examples = [
        (_input_payload(block), _output_payload(block))
        for block in _example_blocks("orchestration_p2/fallback_reviser.md")
    ]

    same_family_input, same_family_output = next(
        pair for pair in examples if len(pair[0]["detected_categories"]) > 1
    )
    labels = same_family_input["detected_categories"]
    assert len(labels) == len(set(labels)) >= 2
    assert {DEFAULT_SPECIALIST_FAMILIES[label] for label in labels} == {
        "response_options_scale"
    }
    assert same_family_input["router_decision"]["decision"] == "fallback"
    assert same_family_input["router_decision"]["recommended_route"] == "fallback"
    assert same_family_output["changed"] is True

    low_confidence_input, low_confidence_output = next(
        pair for pair in examples if pair[0]["router_decision"]["confidence"] < 0.7
    )
    assert low_confidence_input["router_decision"]["decision"] == "fallback"
    assert low_confidence_output["question"] == low_confidence_input["question"]
    assert len(low_confidence_output["response_options"]) == len(
        low_confidence_input["response_options"]
    )

    preserve_input, preserve_output = next(pair for pair in examples if pair[1]["changed"] is False)
    assert preserve_output["question"] == preserve_input["question"]
    assert preserve_output["response_options"] == preserve_input["response_options"]
    assert preserve_input["router_decision"]["decision"] == "fallback"
    preserve_rationale = preserve_output["rationale"].casefold()
    assert "speculative" in preserve_rationale
    assert "unsupported" in preserve_rationale
    fallback_prompt = _p2_path("orchestration_p2/fallback_reviser.md").read_text(
        encoding="utf-8"
    )
    assert "preserve the original when speculative repair is less safe" in fallback_prompt


def test_p2_validator_demos_and_nullable_clean_path_follow_runtime_contract():
    examples = [
        (_input_payload(block), _output_payload(block))
        for block in _example_blocks("orchestration_p2/validator.md")
    ]
    by_status = {output["status"]: (input_payload, output) for input_payload, output in examples}
    assert {"pass", "retry", "manual_review", "failed"} <= set(by_status)

    pass_input, pass_output = by_status["pass"]
    assert pass_input["detected_issues"] == []
    assert pass_output["fixes_detected_issue"] is None
    assert pass_output["retry_instructions"] == []

    retry_input, retry_output = by_status["retry"]
    assert retry_input["detected_issues"]
    assert retry_output["fixes_detected_issue"] is False
    assert retry_output["retry_instructions"]

    review_input, review_output = by_status["manual_review"]
    assert review_input["detected_issues"]
    assert review_output["fixes_detected_issue"] is False
    assert review_output["retry_instructions"] == []

    failed_input, failed_output = by_status["failed"]
    assert isinstance(failed_input["candidate_revision"], dict)
    assert not failed_input["candidate_revision"]["question"].strip()
    assert failed_output["fixes_detected_issue"] is False
    assert failed_output["retry_instructions"] == []

    assert ValidatorResult.from_dict(pass_output).fixes_detected_issue is None
    assert ValidatorResult.from_dict(retry_output).fixes_detected_issue is False
    assert ValidatorResult.from_dict(pass_output).to_dict()["fixes_detected_issue"] is None
    assert ValidatorResult.from_dict(retry_output).to_dict()["fixes_detected_issue"] is False

    prompt = _p2_path("orchestration_p2/validator.md").read_text(encoding="utf-8").casefold()
    assert "`failed` only when" in prompt
    assert "evaluation impossible" in prompt
    assert "never use" in prompt and "candidate is poor" in prompt


def _validator_payload(fixes_detected_issue: bool | None) -> dict[str, Any]:
    return {
        "status": "pass",
        "rationale": "Context-specific schema regression payload.",
        "retry_instructions": [],
        "preserves_construct": True,
        "fixes_detected_issue": fixes_detected_issue,
        "introduces_new_issue": False,
    }


def test_clean_validator_schema_accepts_null_issue_fix_applicability():
    schema = _validator_output_schema(has_detected_issues=False)

    _validate_schema(_validator_payload(None), schema)


def test_clean_validator_schema_rejects_false_issue_fix_applicability():
    schema = _validator_output_schema(has_detected_issues=False)

    with pytest.raises(LLMOutputSchemaError, match="fixes_detected_issue"):
        _validate_schema(_validator_payload(False), schema)


@pytest.mark.parametrize("fixes_detected_issue", [False, True])
def test_detected_issue_validator_schema_accepts_boolean_issue_fix_result(
    fixes_detected_issue: bool,
):
    schema = _validator_output_schema(has_detected_issues=True)

    _validate_schema(_validator_payload(fixes_detected_issue), schema)


def test_detected_issue_validator_schema_rejects_null_issue_fix_result():
    schema = _validator_output_schema(has_detected_issues=True)

    with pytest.raises(LLMOutputSchemaError, match="fixes_detected_issue"):
        _validate_schema(_validator_payload(None), schema)


@pytest.mark.parametrize(
    ("has_detected_issues", "updates", "expected_status"),
    [
        (True, {"preserves_construct": False}, "manual_review"),
        (True, {"fixes_detected_issue": False}, "manual_review"),
        (True, {"introduces_new_issue": True}, "manual_review"),
        (True, {"retry_instructions": ["Repair the issue."]}, "retry"),
        (
            False,
            {"preserves_construct": False, "fixes_detected_issue": None},
            "manual_review",
        ),
        (False, {"fixes_detected_issue": True}, "manual_review"),
        (
            False,
            {"introduces_new_issue": True, "fixes_detected_issue": None},
            "manual_review",
        ),
        (
            False,
            {
                "fixes_detected_issue": None,
                "retry_instructions": ["Repair the issue."],
            },
            "retry",
        ),
    ],
)
def test_validator_pass_invariants_downgrade_contradictory_pass_outputs(
    has_detected_issues: bool,
    updates: dict[str, Any],
    expected_status: str,
):
    payload = _validator_payload(True if has_detected_issues else None)
    payload.update(updates)

    result = ValidatorResult.from_dict(
        payload,
        has_detected_issues=has_detected_issues,
    )

    assert result.status == expected_status
    assert "Contradictory validator pass downgraded" in result.rationale


@pytest.mark.parametrize(
    ("prompt_pack", "orchestration_enabled"),
    [
        ("baseline_codebook", True),
        ("baseline_p1", True),
        ("baseline_p2", True),
        ("orchestration_codebook", False),
        ("orchestration_p1", False),
        ("orchestration_p2", False),
    ],
)
def test_known_prompt_pipeline_mismatches_fail_fast(prompt_pack: str, orchestration_enabled: bool):
    with pytest.raises(ValueError, match="cannot run"):
        ItemReviserPipeline(
            model=NoopLLM(),
            prompt_config={"name": prompt_pack},
            orchestration_config={"enabled": orchestration_enabled},
        )


def test_all_26_manifest_prompt_pipeline_pairs_compose_and_pass_compatibility(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("METRIC_OFFLINE", "true")
    monkeypatch.setenv("METRIC_CACHE_PATH", ".metric-cache")
    monkeypatch.setenv("RUN_NAME", "prompt-contract-test")
    monkeypatch.setenv("HYDRA_OUTPUT_DIR", "outputs/prompt-contract-test")
    rows = load_manifest()
    assert len(rows) == 26

    GlobalHydra.instance().clear()
    try:
        with initialize_config_dir(config_dir=str(REPO_ROOT / "configs"), version_base=None):
            for row in rows:
                cfg = compose(
                    config_name="config",
                    overrides=[
                        *hydra_overrides(row, git_commit="prompt-contract-test"),
                        f"paths.root={REPO_ROOT}",
                    ],
                )
                assert cfg.prompt.name == row["prompt_config"]
                assert bool(cfg.orchestration.enabled) is bool(row["orchestration_enabled"])
                validate_prompt_pipeline_compatibility(
                    cfg.prompt,
                    orchestration_enabled=bool(cfg.orchestration.enabled),
                )
    finally:
        GlobalHydra.instance().clear()


def test_hydra_composed_actual_runtime_prompts_render_without_placeholders():
    context = _render_context()
    rendered_roles: set[tuple[str, str]] = set()

    GlobalHydra.instance().clear()
    try:
        with initialize_config_dir(config_dir=str(REPO_ROOT / "configs"), version_base=None):
            for prompt_pack, orchestration_enabled, roles in TREATMENT_PIPELINES:
                cfg = _compose_prompt_pack(prompt_pack, orchestration_enabled)
                prompt_config = OmegaConf.to_container(cfg.prompt, resolve=True)
                assert isinstance(prompt_config, dict)
                validate_prompt_pipeline_compatibility(
                    prompt_config,
                    orchestration_enabled=orchestration_enabled,
                )
                for role in roles:
                    assert role in prompt_config
                    rendered = AgentPromptConfig.from_config(prompt_config[role]).render(context)
                    assert not UNRESOLVED_PLACEHOLDER_RE.search(rendered), (
                        f"Unresolved prompt placeholder in {prompt_pack}:{role}"
                    )
                    rendered_roles.add((prompt_pack, role))
    finally:
        GlobalHydra.instance().clear()

    expected_count = 3 * len(BASELINE_ROLES) + 3 * len(ORCHESTRATION_ROLES)
    assert len(rendered_roles) == expected_count
