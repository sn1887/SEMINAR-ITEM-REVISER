from __future__ import annotations

from item_reviser.agents.item_reviser import ItemReviserAgent
from item_reviser.agents.orchestration import OrchestratedItemReviser
from item_reviser.agents.quality_checker import QualityCheckerAgent
from item_reviser.models.base import BaseLLM
from item_reviser.orchestration.config import OrchestrationConfig
from item_reviser.prompting import agent_prompt_config
from item_reviser.schemas import PipelineResult, SurveyItem


class ItemReviserPipeline:
    def __init__(
        self,
        model: BaseLLM,
        prompt_config: object,
        orchestration_config: object | None = None,
    ) -> None:
        if model is None:
            raise ValueError("ItemReviserPipeline requires an LLM model.")
        self.orchestration_config = OrchestrationConfig.from_config(orchestration_config)
        self.orchestrator: OrchestratedItemReviser | None = None
        if self.orchestration_config.enabled:
            self.orchestrator = OrchestratedItemReviser(
                model=model,
                prompt_config=prompt_config,
                orchestration_config=self.orchestration_config,
            )
            return

        self.quality_checker = QualityCheckerAgent(
            model=model,
            prompt_config=agent_prompt_config(prompt_config, "quality_checker"),
        )
        self.item_reviser = ItemReviserAgent(
            model=model,
            prompt_config=agent_prompt_config(prompt_config, "item_reviser"),
        )

    def run(self, item: SurveyItem) -> PipelineResult:
        if self.orchestrator is not None:
            return self.orchestrator.run(item)

        errors = self.quality_checker.check(item)
        revised = self.item_reviser.revise(item, errors)
        return PipelineResult(
            item_id=item.id,
            original_item=item,
            detected_errors=errors,
            revised_item=revised,
        )
