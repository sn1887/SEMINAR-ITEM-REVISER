from __future__ import annotations

from abc import ABC

from item_reviser.models.base import BaseLLM


class BaseAgent(ABC):
    def __init__(self, model: BaseLLM | None = None) -> None:
        self.model = model
