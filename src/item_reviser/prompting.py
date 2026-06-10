from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from string import Template
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


def prompt_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


@dataclass(frozen=True)
class AgentPromptConfig:
    template_path: str | None = None
    template: str | None = None
    max_retries: int = 3
    timeout_seconds: float = 120.0

    @classmethod
    def from_config(cls, config: object | None) -> "AgentPromptConfig":
        data = _to_plain_mapping(config)
        return cls(
            template_path=(
                str(data["template_path"]) if data.get("template_path") else None
            ),
            template=str(data["template"]) if data.get("template") else None,
            max_retries=int(data.get("max_retries", 3)),
            timeout_seconds=float(data.get("timeout_seconds", 120.0)),
        )

    def load_template(self) -> str:
        if self.template is not None:
            return self.template
        if self.template_path is None:
            raise ValueError("Prompt config requires either template_path or template.")
        path = Path(self.template_path)
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")
        return path.read_text(encoding="utf-8")

    def render(self, context: Mapping[str, Any]) -> str:
        normalized = {key: prompt_value(value) for key, value in context.items()}
        return Template(self.load_template()).safe_substitute(normalized)


def agent_prompt_config(prompt_config: object, agent_name: str) -> AgentPromptConfig:
    data = _to_plain_mapping(prompt_config)
    if agent_name not in data:
        raise ValueError(f"Missing prompt config for agent '{agent_name}'.")
    return AgentPromptConfig.from_config(data[agent_name])
