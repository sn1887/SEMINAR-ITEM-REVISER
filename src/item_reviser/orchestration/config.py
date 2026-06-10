from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from omegaconf import DictConfig, OmegaConf

from item_reviser.constants import ERROR_CATEGORIES
from item_reviser.schemas import REPAIR_FAMILIES


DEFAULT_SPECIALIST_FAMILIES: dict[str, str] = {
    "leading_question": "wording_clarity",
    "loaded_question": "wording_clarity",
    "double_barreled": "construct_alignment",
    "recall_error": "wording_clarity",
    "vague_ambiguous": "wording_clarity",
    "sensitive_topic_direct": "bias_sensitivity",
    "social_desirability": "bias_sensitivity",
    "negative_wording": "wording_clarity",
    "open_closed_mismatch": "questionnaire_format",
    "agree_disagree_scale": "response_options_scale",
    "unbalanced_scale": "response_options_scale",
    "incomplete_options": "response_options_scale",
    "non_exclusive_options": "response_options_scale",
    "missing_scale_labels": "response_options_scale",
    "too_many_scale_points": "response_options_scale",
    "polarity_mismatch": "response_options_scale",
}


DEFAULT_AGENT_PROMPTS: dict[str, str] = {
    "router": "router",
    "planner": "revision_planner",
    "fallback": "fallback_reviser",
    "validator": "validator",
    "wording_clarity": "wording_clarity",
    "response_options_scale": "response_options_scale",
    "construct_alignment": "construct_alignment",
    "bias_sensitivity": "bias_sensitivity",
    "questionnaire_format": "questionnaire_format",
}


def _to_plain_mapping(config: object | None) -> dict[str, Any]:
    if config is None:
        return {}
    if isinstance(config, DictConfig):
        return dict(OmegaConf.to_container(config, resolve=True))
    if isinstance(config, Mapping):
        return dict(config)
    if hasattr(config, "to_container"):
        return dict(config.to_container(resolve=True))  # type: ignore[call-arg]
    return dict(vars(config))


def _as_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return list(default)


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, DictConfig):
        return dict(OmegaConf.to_container(value, resolve=True))
    if isinstance(value, Mapping):
        return dict(value)
    return dict(vars(value))


@dataclass(frozen=True)
class OrchestrationConfig:
    enabled: bool = False
    strategy: str = "single_specialist"
    taxonomy_labels: list[str] = field(default_factory=lambda: list(ERROR_CATEGORIES))
    confidence_threshold: float = 0.7
    retry_budget: int = 1
    multi_label_strategy: str = "fallback"
    specialist_families: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_SPECIALIST_FAMILIES)
    )
    agent_prompt_names: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_AGENT_PROMPTS))

    @classmethod
    def from_config(cls, config: object | None) -> "OrchestrationConfig":
        data = _to_plain_mapping(config)
        enabled = bool(data.get("enabled", False))
        threshold = float(data.get("confidence_threshold", 0.7))
        if threshold < 0.0 or threshold > 1.0:
            raise ValueError("orchestration.confidence_threshold must be between 0 and 1.")

        retry_budget = int(data.get("retry_budget", 1))
        if retry_budget < 0:
            raise ValueError("orchestration.retry_budget must be zero or greater.")

        strategy = str(data.get("strategy", "single_specialist") or "single_specialist")
        if strategy not in {"single_specialist", "sequential_specialists"}:
            raise ValueError(
                "orchestration.strategy must be 'single_specialist' or "
                "'sequential_specialists'."
            )

        multi_label_strategy = str(
            data.get("multi_label_strategy", "fallback") or "fallback"
        )
        if multi_label_strategy not in {"fallback", "sequential"}:
            raise ValueError(
                "orchestration.multi_label_strategy must be 'fallback' or 'sequential'."
            )

        labels = _as_list(data.get("taxonomy_labels"), list(ERROR_CATEGORIES))
        unsupported_labels = sorted(set(labels) - set(ERROR_CATEGORIES))
        if unsupported_labels:
            raise ValueError(
                "orchestration.taxonomy_labels contains unsupported labels: "
                + ", ".join(unsupported_labels)
            )

        family_data = dict(DEFAULT_SPECIALIST_FAMILIES)
        family_data.update(
            {
                str(key): str(value)
                for key, value in _as_mapping(data.get("specialist_families")).items()
            }
        )
        invalid_family_labels = sorted(set(family_data) - set(ERROR_CATEGORIES))
        if invalid_family_labels:
            raise ValueError(
                "orchestration.specialist_families contains unsupported labels: "
                + ", ".join(invalid_family_labels)
            )
        invalid_families = sorted(set(family_data.values()) - REPAIR_FAMILIES)
        if invalid_families:
            raise ValueError(
                "orchestration.specialist_families contains unsupported families: "
                + ", ".join(invalid_families)
            )

        prompt_names = dict(DEFAULT_AGENT_PROMPTS)
        prompt_names.update(
            {
                str(key): str(value)
                for key, value in _as_mapping(data.get("agent_prompt_names")).items()
            }
        )

        return cls(
            enabled=enabled,
            strategy=strategy,
            taxonomy_labels=labels,
            confidence_threshold=threshold,
            retry_budget=retry_budget,
            multi_label_strategy=multi_label_strategy,
            specialist_families=family_data,
            agent_prompt_names=prompt_names,
        )

    def prompt_name(self, role: str) -> str:
        try:
            return self.agent_prompt_names[role]
        except KeyError as exc:
            raise ValueError(f"Missing orchestration prompt mapping for role '{role}'.") from exc

    def family_for_label(self, taxonomy_label: str) -> str | None:
        return self.specialist_families.get(taxonomy_label)
