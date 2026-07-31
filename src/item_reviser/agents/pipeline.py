from __future__ import annotations

from item_reviser.agent_config import AgentRuntimeConfig
from item_reviser.agents.item_reviser import ItemReviserAgent
from item_reviser.agents.orchestration import OrchestratedItemReviser
from item_reviser.agents.quality_checker import QualityCheckerAgent
from item_reviser.models.base import BaseLLM
from item_reviser.orchestration.config import OrchestrationConfig
from item_reviser.prompting import (
    agent_prompt_config,
    validate_prompt_pipeline_compatibility,
)
from item_reviser.schemas import PipelineResult, RevisedItem, SurveyItem


class ItemReviserPipeline:
    def __init__(
        self,
        model: BaseLLM,
        prompt_config: object,
        agent_config: object | None = None,
        orchestration_config: object | None = None,
    ) -> None:
        if model is None:
            raise ValueError("ItemReviserPipeline requires an LLM model.")
        self.agent_config = AgentRuntimeConfig.from_config(agent_config)
        self.orchestration_config = OrchestrationConfig.from_config(orchestration_config)
        validate_prompt_pipeline_compatibility(
            prompt_config,
            orchestration_enabled=self.orchestration_config.enabled,
        )
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

        errors = []
        if self.agent_config.use_llm_for_quality_checking:
            errors = self.quality_checker.check(item)

        if self.agent_config.use_llm_for_revision and (
            errors or not self.agent_config.skip_revision_when_no_errors
        ):
            revised = self.item_reviser.revise(item, errors)
        else:
            revised = RevisedItem(
                question=item.question,
                response_options=list(item.response_options),
                revision_notes=list(self.agent_config.unchanged_revision_notes),
                changed=False,
            )
        return PipelineResult(
            item_id=item.id,
            original_item=item,
            detected_errors=errors,
            revised_item=revised,
        )
