from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from omegaconf import DictConfig, OmegaConf


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


def _as_str_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return list(default)


@dataclass(frozen=True)
class AgentRuntimeConfig:
    use_llm_for_quality_checking: bool = True
    use_llm_for_revision: bool = True
    skip_revision_when_no_errors: bool = True
    unchanged_revision_notes: list[str] = field(
        default_factory=lambda: ["No issues detected; item left unchanged."]
    )

    @classmethod
    def from_config(cls, config: object | None) -> "AgentRuntimeConfig":
        data = _to_plain_mapping(config)
        return cls(
            use_llm_for_quality_checking=bool(data.get("use_llm_for_quality_checking", True)),
            use_llm_for_revision=bool(data.get("use_llm_for_revision", True)),
            skip_revision_when_no_errors=bool(data.get("skip_revision_when_no_errors", True)),
            unchanged_revision_notes=_as_str_list(
                data.get("unchanged_revision_notes"),
                ["No issues detected; item left unchanged."],
            ),
        )
