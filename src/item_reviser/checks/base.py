from __future__ import annotations

from abc import ABC, abstractmethod

from item_reviser.schemas import CheckResult, SurveyItem


class BaseChecker(ABC):
    name: str = "base"

    @abstractmethod
    def check(self, item: SurveyItem) -> list[CheckResult]:
        raise NotImplementedError
