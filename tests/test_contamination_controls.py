import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import yaml

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.models.base import BaseLLM
from item_reviser.prompting import AgentPromptConfig
from item_reviser.schemas import SurveyItem

REPO_ROOT = Path(__file__).resolve().parents[1]
V4_DATASET = REPO_ROOT / "data/final_gold_200_v4/final_gold_200_unique_v4.jsonl"
PROMPT_CONFIGS = (
    "baseline_p1",
    "baseline_p2",
    "orchestration_p1",
    "orchestration_p2",
)
BANNED_PROMPT_KEYS = {"item_id", "target_concept", "topic"}
BANNED_PROMPT_TEXT = {
    "candidate-v1-single-leading-question-001",
    "LEAK_TARGET_CONCEPT",
    "LEAK_TOPIC",
    "known_errors",
    "expected_revision",
    "review_notes",
    "target_concept",
    "item_id",
    "- id:",
}
P2_EXAMPLE_RE = re.compile(
    r"<!-- P2_EXAMPLE_START -->(.*?)<!-- P2_EXAMPLE_END -->",
    flags=re.DOTALL,
)
FENCED_JSON_RE = re.compile(r"```json\s*(.*?)\s*```", flags=re.DOTALL | re.IGNORECASE)
GENERIC_SCALE_TOKENS = {
    "agree",
    "applicable",
    "completely",
    "day",
    "days",
    "disagree",
    "extremely",
    "more",
    "most",
    "much",
    "neither",
    "never",
    "no",
    "none",
    "nor",
    "not",
    "often",
    "or",
    "rarely",
    "sometimes",
    "somewhat",
    "strongly",
    "very",
    "yes",
}


class CapturingLLM(BaseLLM):
    backend_name = "capturing"

    def __init__(self, responses: list[dict[str, object]]) -> None:
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
        _ = timeout_seconds, kwargs
        self.prompts.append(prompt)
        return json.dumps(self.responses.pop(0))


def _template(path: str) -> dict[str, object]:
    return {
        "template_path": str(REPO_ROOT / path),
        "max_retries": 1,
        "timeout_seconds": 10,
    }


def _baseline_prompt_config() -> dict[str, object]:
    return {
        "quality_checker": _template("prompts/agents/baseline/quality_checker.md"),
        "item_reviser": _template("prompts/agents/baseline/item_reviser.md"),
    }


def _orchestration_prompt_config() -> dict[str, object]:
    return {
        "router": _template("prompts/agents/orchestration/router.md"),
        "revision_planner": _template("prompts/agents/orchestration/revision_planner.md"),
        "fallback_reviser": _template("prompts/agents/orchestration/fallback_reviser.md"),
        "validator": _template("prompts/agents/orchestration/validator.md"),
        "wording_clarity": _template("prompts/agents/orchestration/specialist_wording_clarity.md"),
        "response_options_scale": _template(
            "prompts/agents/orchestration/specialist_response_options_scale.md"
        ),
        "construct_alignment": _template(
            "prompts/agents/orchestration/specialist_construct_alignment.md"
        ),
        "bias_sensitivity": _template(
            "prompts/agents/orchestration/specialist_bias_sensitivity.md"
        ),
        "questionnaire_format": _template(
            "prompts/agents/orchestration/specialist_questionnaire_format.md"
        ),
    }


def _leaky_item() -> SurveyItem:
    return SurveyItem(
        id="candidate-v1-single-leading-question-001",
        question="How satisfied are you with the service?",
        response_options=["Very dissatisfied", "Very satisfied"],
        target_concept="LEAK_TARGET_CONCEPT",
        topic="LEAK_TOPIC",
        known_errors=["leading_question"],
        is_flawed=True,
        expected_revision={"question": "LEAK_EXPECTED_REVISION"},
        metadata={"review_notes": "LEAK_REVIEW_NOTES"},
    )


def _assert_no_prompt_leak(prompts: list[str]) -> None:
    rendered = "\n\n".join(prompts)
    for banned in BANNED_PROMPT_TEXT:
        assert banned not in rendered


def _normalize_prompt_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _v4_reference_texts() -> list[tuple[str, str, str]]:
    references: list[tuple[str, str, str]] = []
    for line in V4_DATASET.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        item_id = str(row["id"])
        references.append(("question", f"{item_id}:candidate_question", row["question"]))
        references.append(
            (
                "response_options",
                f"{item_id}:candidate_response_options",
                " | ".join(str(option) for option in row.get("response_options", [])),
            )
        )
        revision = row.get("expected_revision", {})
        if isinstance(revision, dict):
            expected_question = revision.get("question")
            if isinstance(expected_question, str):
                references.append(
                    ("question", f"{item_id}:expected_question", expected_question)
                )
            expected_options = revision.get("response_options")
            if isinstance(expected_options, list):
                references.append(
                    (
                        "response_options",
                        f"{item_id}:expected_response_options",
                        " | ".join(str(option) for option in expected_options),
                    )
                )
    return references


def _collect_item_fields(value: object) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    if isinstance(value, dict):
        question = value.get("question")
        if isinstance(question, str):
            fields.append(("question", question))
        response_options = value.get("response_options")
        if isinstance(response_options, list):
            fields.append(
                ("response_options", " | ".join(str(option) for option in response_options))
            )
        for nested in value.values():
            fields.extend(_collect_item_fields(nested))
    elif isinstance(value, list):
        for nested in value:
            fields.extend(_collect_item_fields(nested))
    return fields


def _p2_complete_example_fields() -> list[tuple[str, str, str]]:
    examples: list[tuple[str, str, str]] = []
    for pack in ("baseline_p2", "orchestration_p2"):
        for path in (REPO_ROOT / "prompts/agents" / pack).glob("*.md"):
            text = path.read_text(encoding="utf-8")
            starts = text.count("<!-- P2_EXAMPLE_START -->")
            ends = text.count("<!-- P2_EXAMPLE_END -->")
            blocks = P2_EXAMPLE_RE.findall(text)
            assert starts == ends == len(blocks), f"Unbalanced P2 examples in {path}"
            for index, block in enumerate(blocks, start=1):
                fields: list[tuple[str, str]] = []
                for raw_payload in FENCED_JSON_RE.findall(block):
                    fields.extend(_collect_item_fields(json.loads(raw_payload)))

                # Router and questionnaire-format examples intentionally use a
                # readable text input. Extract whole question/option fields from
                # that complete marked example rather than comparing isolated lines.
                for question in re.findall(r"(?m)^\s*question:\s*(.+?)\s*$", block):
                    fields.append(("question", question.strip()))
                for raw_options in re.findall(
                    r"(?m)^\s*response_options:\s*(\[[^\n]*\])\s*$", block
                ):
                    options = json.loads(raw_options)
                    fields.append(
                        ("response_options", " | ".join(str(option) for option in options))
                    )

                location = f"{path.relative_to(REPO_ROOT)} example {index}"
                for kind, value in dict.fromkeys(fields):
                    examples.append((kind, location, value))
    return examples


def _is_substantive_for_overlap(value: str) -> bool:
    normalized = _normalize_prompt_text(value)
    informative = [
        token
        for token in normalized.split()
        if token not in GENERIC_SCALE_TOKENS and not token.isdigit()
    ]
    return len(normalized) >= 24 and len(set(informative)) >= 4


def test_baseline_prompts_and_contexts_exclude_gold_fields(monkeypatch):
    contexts: list[dict[str, object]] = []
    original_render = AgentPromptConfig.render

    def capture_context(self: AgentPromptConfig, context: dict[str, object]) -> str:
        contexts.append(dict(context))
        return original_render(self, context)

    monkeypatch.setattr(AgentPromptConfig, "render", capture_context)
    model = CapturingLLM(
        [
            {
                "errors": [
                    {
                        "category": "leading_question",
                        "severity": "high",
                        "explanation": "Leading wording.",
                    }
                ]
            },
            {
                "question": "How satisfied are you with the service?",
                "response_options": ["Very dissatisfied", "Very satisfied"],
                "revision_notes": ["No gold fields used."],
                "changed": False,
            },
        ]
    )

    ItemReviserPipeline(
        model=model,
        prompt_config=_baseline_prompt_config(),
    ).run(_leaky_item())

    assert contexts
    for context in contexts:
        assert BANNED_PROMPT_KEYS.isdisjoint(context)
        for issue in context.get("detected_issues", []) or []:
            if isinstance(issue, dict) and issue.get("checker") == "llm_router":
                assert "severity" not in issue
    _assert_no_prompt_leak(model.prompts)


def test_orchestration_prompts_and_contexts_exclude_gold_fields(monkeypatch):
    contexts: list[dict[str, object]] = []
    original_render = AgentPromptConfig.render

    def capture_context(self: AgentPromptConfig, context: dict[str, object]) -> str:
        contexts.append(dict(context))
        return original_render(self, context)

    monkeypatch.setattr(AgentPromptConfig, "render", capture_context)
    model = CapturingLLM(
        [
            {
                "decision": "revise",
                "taxonomy_labels": ["leading_question"],
                "confidence": 0.9,
                "evidence": "question wording",
                "rationale": "A revision is needed.",
                "recommended_route": "wording_clarity",
            },
            {
                "repair_family": "wording_clarity",
                "selected_agent": "wording_clarity",
                "instructions": ["Use neutral wording."],
                "rationale": "Use the wording specialist.",
            },
            {
                "question": "How satisfied are you with the service?",
                "response_options": ["Very dissatisfied", "Very satisfied"],
                "revision_notes": ["Neutral wording."],
                "changed": False,
                "rationale": "The candidate is neutral.",
            },
            {
                "status": "pass",
                "rationale": "Valid revision.",
                "retry_instructions": [],
                "preserves_construct": True,
                "fixes_detected_issue": True,
                "introduces_new_issue": False,
            },
        ]
    )

    ItemReviserPipeline(
        model=model,
        prompt_config=_orchestration_prompt_config(),
        orchestration_config={"enabled": True},
    ).run(_leaky_item())

    assert contexts
    for context in contexts:
        assert BANNED_PROMPT_KEYS.isdisjoint(context)
        for issue in context.get("detected_issues", []) or []:
            if isinstance(issue, dict) and issue.get("checker") == "llm_router":
                assert "severity" not in issue
    _assert_no_prompt_leak(model.prompts)


def test_agent_prompt_templates_have_no_banned_placeholders():
    prompt_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO_ROOT / "prompts" / "agents").rglob("*.md")
    )

    for banned in (
        "${item_id}",
        "${target_concept}",
        "${topic}",
        "${known_errors}",
        "${is_flawed}",
        "${expected_revision}",
        "${metadata}",
        "${review_notes}",
    ):
        assert banned not in prompt_text


def test_p1_p2_prompt_configs_are_opt_in_and_resolve_existing_templates():
    default_config = yaml.safe_load(
        (REPO_ROOT / "configs/prompt/default.yaml").read_text(encoding="utf-8")
    )
    assert default_config["name"] == "default"

    for name in PROMPT_CONFIGS:
        config = yaml.safe_load(
            (REPO_ROOT / "configs/prompt" / f"{name}.yaml").read_text(encoding="utf-8")
        )
        assert config["name"] == name
        for agent_config in config.values():
            if not isinstance(agent_config, dict) or "template_path" not in agent_config:
                continue
            template_path = agent_config["template_path"]
            relative_path = template_path.removeprefix("${paths.prompt_dir}/")
            assert (REPO_ROOT / "prompts" / relative_path).is_file()

    assert "_p1/" not in "\n".join(
        str(value) for value in default_config.values()
    )
    assert "_p2/" not in "\n".join(
        str(value) for value in default_config.values()
    )


def test_complete_p2_examples_pass_v4_lexical_contamination_screen():
    """Screen all four benchmark text surfaces; this is not proof against semantic leakage."""

    references = _v4_reference_texts()
    examples = _p2_complete_example_fields()
    reference_locations = {location.rsplit(":", 1)[-1] for _, location, _ in references}
    assert reference_locations == {
        "candidate_question",
        "candidate_response_options",
        "expected_question",
        "expected_response_options",
    }
    assert examples

    for kind, example_location, example in examples:
        if not _is_substantive_for_overlap(example):
            # Short generic labels such as "Never" and count scales are survey
            # vocabulary, not useful evidence of contamination.
            continue
        normalized_example = _normalize_prompt_text(example)
        for reference_kind, reference_location, reference in references:
            if reference_kind != kind or not _is_substantive_for_overlap(reference):
                continue
            normalized_reference = _normalize_prompt_text(reference)
            assert normalized_example != normalized_reference, (
                "P2 complete example contains a normalized exact benchmark match: "
                f"{example_location} vs {reference_location}"
            )
            similarity = SequenceMatcher(
                None, normalized_example, normalized_reference
            ).ratio()
            assert similarity < 0.85, (
                "P2 complete example is too lexically similar to a v4 benchmark field: "
                f"{example_location} vs {reference_location} ({similarity:.3f}); "
                f"{example!r} vs {reference!r}"
            )


def test_p1_p2_templates_contain_no_forbidden_inference_placeholders():
    prompt_paths = [
        path
        for pack in ("baseline_p1", "baseline_p2", "orchestration_p1", "orchestration_p2")
        for path in (REPO_ROOT / "prompts/agents" / pack).glob("*.md")
    ]
    assert prompt_paths
    prompt_text = "\n".join(path.read_text(encoding="utf-8") for path in prompt_paths)

    for banned in (
        "${item_id}",
        "${target_concept}",
        "${topic}",
        "${known_errors}",
        "${is_flawed}",
        "${expected_revision}",
        "${metadata}",
        "${review_notes}",
    ):
        assert banned not in prompt_text


def _taxonomy_boundary_lines(relative_path: str) -> list[str]:
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    _, marker, tail = text.partition("Taxonomy boundary rules:")
    assert marker, f"Missing taxonomy section in {relative_path}"
    section = tail.partition("Return strict JSON only.")[0]
    return [line.strip() for line in section.splitlines() if line.strip().startswith("- `")]


def _assert_contains_all(target_relative_path: str, snippets: list[str]) -> None:
    target = (REPO_ROOT / target_relative_path).read_text(encoding="utf-8")
    for snippet in snippets:
        assert snippet in target, f"Missing P0 snippet in {target_relative_path}: {snippet}"


def test_p1_p2_prompt_ablation_preserves_p0_codebook_content():
    baseline_taxonomy = _taxonomy_boundary_lines(
        "prompts/agents/baseline_codebook/quality_checker.md"
    )
    orchestration_taxonomy = _taxonomy_boundary_lines(
        "prompts/agents/orchestration_codebook/router.md"
    )
    baseline_quality_snippets = [
        "Decision protocol:",
        "Judge only the visible question and response options.",
        "If no defect is present, return no errors.",
        "Do not flag an item merely because it could be stylistically improved.",
        "Severity definitions:",
        "Calibrate severity by likely impact on respondent interpretation and measurement validity",
        *baseline_taxonomy,
    ]
    baseline_reviser_snippets = [
        "Severity interpretation:",
        "Revision principles:",
        "Preserve the construct expressed by the item.",
        "Fix only the detected, independently supported problems.",
        "If no defect is present, preserve the item unchanged and set `changed` to false.",
        "If the detected evidence does not establish a real taxonomy issue",
    ]
    orchestration_router_snippets = [
        "Decision protocol:",
        "Return `accept` when the item is already a sound questionnaire item.",
        "Return `fallback` for low-confidence, ambiguous, mixed, unsupported",
        "If no defect is present, return no taxonomy labels and recommend `accept`.",
        "The router output has no severity field.",
        "Do not assign or claim to predict",
        *orchestration_taxonomy,
    ]
    orchestration_fallback_snippets = [
        "Revision principles:",
        "Preserve the construct and measurement focus expressed by the question and options.",
        "Fix only issues supported by the item and router evidence.",
        "If no defect is present or the evidence does not establish a real taxonomy issue",
    ]

    for pack in ("baseline_p1", "baseline_p2"):
        _assert_contains_all(
            f"prompts/agents/{pack}/quality_checker.md",
            baseline_quality_snippets,
        )
        _assert_contains_all(
            f"prompts/agents/{pack}/item_reviser.md",
            baseline_reviser_snippets,
        )
    for pack in ("orchestration_p1", "orchestration_p2"):
        _assert_contains_all(
            f"prompts/agents/{pack}/router.md",
            orchestration_router_snippets,
        )
        _assert_contains_all(
            f"prompts/agents/{pack}/fallback_reviser.md",
            orchestration_fallback_snippets,
        )


def test_p2_prompt_ablation_contains_p1_rules_plus_fixed_examples():
    p1_p2_pairs = [
        ("baseline_p1/quality_checker.md", "baseline_p2/quality_checker.md"),
        ("baseline_p1/item_reviser.md", "baseline_p2/item_reviser.md"),
        ("orchestration_p1/router.md", "orchestration_p2/router.md"),
        ("orchestration_p1/fallback_reviser.md", "orchestration_p2/fallback_reviser.md"),
        (
            "orchestration_p1/specialist_response_options_scale.md",
            "orchestration_p2/specialist_response_options_scale.md",
        ),
        (
            "orchestration_p1/specialist_questionnaire_format.md",
            "orchestration_p2/specialist_questionnaire_format.md",
        ),
        ("orchestration_p1/validator.md", "orchestration_p2/validator.md"),
    ]

    for p1_relative_path, p2_relative_path in p1_p2_pairs:
        p1_text = (REPO_ROOT / "prompts/agents" / p1_relative_path).read_text(
            encoding="utf-8"
        )
        p2_text = (REPO_ROOT / "prompts/agents" / p2_relative_path).read_text(
            encoding="utf-8"
        )
        p1_operational_body = p1_text.rsplit("Return strict JSON only.", maxsplit=1)[0].rstrip()
        assert p1_operational_body in p2_text
        assert (
            "Fixed calibration examples, authored from general survey-design principles:"
            in p2_text
        )
