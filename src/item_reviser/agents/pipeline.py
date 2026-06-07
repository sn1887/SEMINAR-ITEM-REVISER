from __future__ import annotations

from item_reviser.agents.item_reviser import ItemReviserAgent
from item_reviser.agents.quality_checker import QualityCheckerAgent
from item_reviser.models.base import BaseLLM
from item_reviser.schemas import PipelineResult, SurveyItem


class ItemReviserPipeline:
    def __init__(self, model: BaseLLM | None = None) -> None:
        self.quality_checker = QualityCheckerAgent(model=model)
        self.item_reviser = ItemReviserAgent(model=model)

    def run(self, item: SurveyItem) -> PipelineResult:
        errors = self.quality_checker.check(item)
        revised = self.item_reviser.revise(item, errors)
        return PipelineResult(
            item_id=item.id,
            original_item=item,
            detected_errors=errors,
            revised_item=revised,
        )
