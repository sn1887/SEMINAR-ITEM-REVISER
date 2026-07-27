from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from item_reviser.agents.base import BaseAgent
from item_reviser.constants import CATEGORY_DESCRIPTIONS, ERROR_CATEGORIES
from item_reviser.models.base import BaseLLM
from item_reviser.orchestration.config import OrchestrationConfig
from item_reviser.prompting import AgentPromptConfig, agent_prompt_config
from item_reviser.schemas import (
    CheckResult,
    OrchestrationTrace,
    PipelineResult,
    REPAIR_FAMILIES,
    ReviserAgentOutput,
    RevisedItem,
    RevisionPlan,
    RouterDecision,
    SurveyItem,
    ValidatorResult,
)


ROUTER_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "decision",
        "taxonomy_labels",
        "confidence",
        "evidence",
        "rationale",
        "recommended_route",
    ],
    "additionalProperties": False,
    "properties": {
        "decision": {"type": "string", "enum": ["accept", "revise", "fallback"]},
        "taxonomy_labels": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "evidence": {"type": ["string", "null"]},
        "rationale": {"type": "string"},
        "recommended_route": {"type": "string"},
    },
}


REVISION_PLAN_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["repair_family", "selected_agent", "instructions", "rationale"],
    "additionalProperties": False,
    "properties": {
        "repair_family": {
            "type": "string",
            "enum": sorted(REPAIR_FAMILIES),
        },
        "selected_agent": {"type": "string"},
        "instructions": {"type": "array", "items": {"type": "string"}},
        "fallback_reason": {"type": ["string", "null"]},
        "rationale": {"type": "string"},
    },
}


ORCHESTRATED_REVISER_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["question", "response_options", "revision_notes", "changed", "rationale"],
    "additionalProperties": False,
    "properties": {
        "question": {"type": "string"},
        "response_options": {"type": "array", "items": {"type": "string"}},
        "revision_notes": {"type": "array", "items": {"type": "string"}},
        "changed": {"type": "boolean"},
        "rationale": {"type": "string"},
    },
}


VALIDATOR_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "status",
        "rationale",
        "retry_instructions",
        "preserves_construct",
        "fixes_detected_issue",
        "introduces_new_issue",
    ],
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["pass", "retry", "manual_review", "failed"],
        },
        "rationale": {"type": "string"},
        "retry_instructions": {"type": "array", "items": {"type": "string"}},
        "preserves_construct": {"type": "boolean"},
        "fixes_detected_issue": {"type": "boolean"},
        "introduces_new_issue": {"type": "boolean"},
    },
}


SPECIALIST_SCOPES = {
    "wording_clarity": (
        "Wording, clarity, leading or loaded phrasing, recall burden, vague terms, "
        "negative wording, and double-barreled phrasing."
    ),
    "response_options_scale": (
        "Response options and scales, including agree/disagree scales, balance, "
        "completeness, exclusivity, labels, point counts, and polarity."
    ),
    "construct_alignment": (
        "Construct preservation and alignment using only the item text and options."
    ),
    "bias_sensitivity": (
        "Sensitive subject matter, social desirability pressure, privacy, "
        "normalization, and respondent comfort."
    ),
    "questionnaire_format": (
        "Questionnaire format fit, especially open/closed response mode alignment."
    ),
}


def _format_allowed_categories(labels: list[str] | None = None) -> str:
    selected = labels or list(ERROR_CATEGORIES)
    rows = [
        {
            "category": category,
            "description": CATEGORY_DESCRIPTIONS.get(category, ""),
        }
        for category in selected
    ]
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _known_taxonomy_labels(labels: list[str], allowed_labels: list[str]) -> list[str]:
    allowed = set(allowed_labels)
    known: list[str] = []
    for label in labels:
        if label in allowed and label not in known:
            known.append(label)
    return known


def _trace_context(trace: OrchestrationTrace) -> dict[str, Any]:
    return {
        "route": trace.route,
        "selected_agent": trace.selected_agent,
        "retry_count": trace.retry_count,
        "validation_status": trace.validation_status,
        "final_status": trace.final_status,
        "fallback_reason": trace.fallback_reason,
        "manual_review_reason": trace.manual_review_reason,
    }


def _candidate_revision_payload(candidate: RevisedItem | ReviserAgentOutput) -> dict[str, Any]:
    return {
        "question": candidate.question,
        "response_options": list(candidate.response_options),
        "revision_notes": list(candidate.revision_notes),
        "changed": bool(candidate.changed),
    }


def _validation_criteria(detected_errors: list[CheckResult]) -> list[str]:
    if not detected_errors:
        return [
            "The original item is acceptable as an unchanged questionnaire item.",
            "The candidate preserves the construct expressed by the original item.",
            "The candidate introduces no obvious questionnaire-quality issue.",
        ]
    return [
        "The candidate fixes the detected issue.",
        "The candidate preserves the construct expressed by the original item.",
        "The candidate introduces no obvious new questionnaire-quality issue.",
    ]


def _unchanged_item(
    item: SurveyItem,
    *,
    note: str,
) -> RevisedItem:
    return RevisedItem(
        question=item.question,
        response_options=list(item.response_options),
        revision_notes=[note],
        changed=False,
    )


class RouterAgent(BaseAgent):
    def __init__(
        self,
        model: BaseLLM,
        prompt_config: AgentPromptConfig,
        orchestration_config: OrchestrationConfig,
    ) -> None:
        super().__init__(model=model)
        self.prompt_config = prompt_config
        self.orchestration_config = orchestration_config

    def route(self, item: SurveyItem) -> RouterDecision:
        prompt = self.prompt_config.render(
            {
                "allowed_categories": _format_allowed_categories(
                    self.orchestration_config.taxonomy_labels
                ),
                "category_descriptions": CATEGORY_DESCRIPTIONS,
                "output_schema": ROUTER_OUTPUT_SCHEMA,
                "allowed_routes": ["accept", "revise", "fallback"],
                "repair_families": sorted(REPAIR_FAMILIES),
                "confidence_threshold": self.orchestration_config.confidence_threshold,
                **item.model_input(),
            }
        )
        payload = self.model.complete_json(
            prompt,
            ROUTER_OUTPUT_SCHEMA,
            max_retries=self.prompt_config.max_retries,
            timeout_seconds=self.prompt_config.timeout_seconds,
        )
        return RouterDecision.from_dict(payload)


class RevisionPlannerAgent(BaseAgent):
    def __init__(self, model: BaseLLM, prompt_config: AgentPromptConfig) -> None:
        super().__init__(model=model)
        self.prompt_config = prompt_config

    def plan(
        self,
        item: SurveyItem,
        router_decision: RouterDecision,
        detected_errors: list[CheckResult],
        *,
        suggested_repair_family: str,
        suggested_agent: str,
        retry_instructions: list[str] | None = None,
        trace: OrchestrationTrace | None = None,
    ) -> RevisionPlan:
        prompt = self.prompt_config.render(
            {
                "output_schema": REVISION_PLAN_OUTPUT_SCHEMA,
                "allowed_categories": _format_allowed_categories(),
                "repair_families": sorted(REPAIR_FAMILIES),
                "suggested_repair_family": suggested_repair_family,
                "suggested_agent": suggested_agent,
                **item.model_input(),
                "router_decision": router_decision.to_dict(),
                "detected_categories": [error.category for error in detected_errors],
                "detected_issues": [error.to_dict() for error in detected_errors],
                "retry_instructions": retry_instructions or [],
                "trace_context": _trace_context(trace) if trace is not None else {},
            }
        )
        payload = self.model.complete_json(
            prompt,
            REVISION_PLAN_OUTPUT_SCHEMA,
            max_retries=self.prompt_config.max_retries,
            timeout_seconds=self.prompt_config.timeout_seconds,
        )
        plan = RevisionPlan.from_dict(payload)
        if not plan.instructions:
            plan.instructions = [
                "Fix the routed questionnaire-design issue.",
                "Preserve the construct expressed by the original item.",
            ]
        return plan


class FallbackReviserAgent(BaseAgent):
    def __init__(self, model: BaseLLM, prompt_config: AgentPromptConfig) -> None:
        super().__init__(model=model)
        self.prompt_config = prompt_config

    def revise(
        self,
        item: SurveyItem,
        detected_errors: list[CheckResult],
        router_decision: RouterDecision,
        *,
        fallback_reason: str,
        retry_instructions: list[str] | None = None,
        retry_count: int = 0,
        trace: OrchestrationTrace | None = None,
    ) -> ReviserAgentOutput:
        prompt = self.prompt_config.render(
            {
                "output_schema": ORCHESTRATED_REVISER_OUTPUT_SCHEMA,
                "allowed_categories": _format_allowed_categories(),
                **item.model_input(),
                "detected_categories": [error.category for error in detected_errors],
                "detected_issues": [error.to_dict() for error in detected_errors],
                "router_decision": router_decision.to_dict(),
                "router_confidence": router_decision.confidence,
                "recommended_route": router_decision.recommended_route,
                "fallback_reason": fallback_reason,
                "retry_instructions": retry_instructions or [],
                "retry_count": retry_count,
                "trace_context": _trace_context(trace) if trace is not None else {},
            }
        )
        payload = self.model.complete_json(
            prompt,
            ORCHESTRATED_REVISER_OUTPUT_SCHEMA,
            max_retries=self.prompt_config.max_retries,
            timeout_seconds=self.prompt_config.timeout_seconds,
        )
        return ReviserAgentOutput.from_dict(
            payload,
            original_item=item,
            agent_name="fallback_reviser",
        )


class SpecialistReviserAgent(BaseAgent):
    def __init__(
        self,
        model: BaseLLM,
        prompt_config: AgentPromptConfig,
        *,
        family: str,
        specialist_name: str,
    ) -> None:
        super().__init__(model=model)
        self.prompt_config = prompt_config
        self.family = family
        self.specialist_name = specialist_name

    def revise(
        self,
        item: SurveyItem,
        detected_errors: list[CheckResult],
        router_decision: RouterDecision,
        revision_plan: RevisionPlan,
        *,
        retry_instructions: list[str] | None = None,
        retry_count: int = 0,
        trace: OrchestrationTrace | None = None,
    ) -> ReviserAgentOutput:
        prompt = self.prompt_config.render(
            {
                "output_schema": ORCHESTRATED_REVISER_OUTPUT_SCHEMA,
                "allowed_categories": _format_allowed_categories(),
                "specialist_name": self.specialist_name,
                "specialist_scope": SPECIALIST_SCOPES.get(self.family, self.family),
                "repair_family": self.family,
                **item.model_input(),
                "detected_categories": [error.category for error in detected_errors],
                "detected_issues": [error.to_dict() for error in detected_errors],
                "router_decision": router_decision.to_dict(),
                "revision_plan": revision_plan.to_dict(),
                "retry_instructions": retry_instructions or [],
                "retry_count": retry_count,
                "trace_context": _trace_context(trace) if trace is not None else {},
            }
        )
        payload = self.model.complete_json(
            prompt,
            ORCHESTRATED_REVISER_OUTPUT_SCHEMA,
            max_retries=self.prompt_config.max_retries,
            timeout_seconds=self.prompt_config.timeout_seconds,
        )
        return ReviserAgentOutput.from_dict(
            payload,
            original_item=item,
            agent_name=self.specialist_name,
        )


class ValidatorAgent(BaseAgent):
    def __init__(self, model: BaseLLM, prompt_config: AgentPromptConfig) -> None:
        super().__init__(model=model)
        self.prompt_config = prompt_config

    def validate(
        self,
        item: SurveyItem,
        detected_errors: list[CheckResult],
        router_decision: RouterDecision,
        candidate: RevisedItem | ReviserAgentOutput,
        *,
        revision_plan: RevisionPlan | None = None,
        remaining_retry_budget: int = 0,
        trace: OrchestrationTrace | None = None,
    ) -> ValidatorResult:
        prompt = self.prompt_config.render(
            {
                "output_schema": VALIDATOR_OUTPUT_SCHEMA,
                "allowed_categories": _format_allowed_categories(),
                "validation_criteria": _validation_criteria(detected_errors),
                **item.model_input(),
                "detected_categories": [error.category for error in detected_errors],
                "detected_issues": [error.to_dict() for error in detected_errors],
                "router_decision": router_decision.to_dict(),
                "revision_plan": revision_plan.to_dict() if revision_plan is not None else {},
                "candidate_revision": _candidate_revision_payload(candidate),
                "remaining_retry_budget": remaining_retry_budget,
                "trace_context": _trace_context(trace) if trace is not None else {},
            }
        )
        payload = self.model.complete_json(
            prompt,
            VALIDATOR_OUTPUT_SCHEMA,
            max_retries=self.prompt_config.max_retries,
            timeout_seconds=self.prompt_config.timeout_seconds,
        )
        return ValidatorResult.from_dict(payload)


class OrchestratedItemReviser:
    def __init__(
        self,
        model: BaseLLM,
        prompt_config: object,
        orchestration_config: OrchestrationConfig,
    ) -> None:
        self.model = model
        self.prompt_config = prompt_config
        self.config = orchestration_config
        self.router = RouterAgent(
            model=model,
            prompt_config=agent_prompt_config(
                prompt_config,
                self.config.prompt_name("router"),
            ),
            orchestration_config=self.config,
        )
        self.planner = RevisionPlannerAgent(
            model=model,
            prompt_config=agent_prompt_config(
                prompt_config,
                self.config.prompt_name("planner"),
            ),
        )
        self.fallback_reviser = FallbackReviserAgent(
            model=model,
            prompt_config=agent_prompt_config(
                prompt_config,
                self.config.prompt_name("fallback"),
            ),
        )
        self.validator = ValidatorAgent(
            model=model,
            prompt_config=agent_prompt_config(
                prompt_config,
                self.config.prompt_name("validator"),
            ),
        )
        self.specialists = {
            family: SpecialistReviserAgent(
                model=model,
                prompt_config=agent_prompt_config(prompt_config, self.config.prompt_name(family)),
                family=family,
                specialist_name=self.config.prompt_name(family),
            )
            for family in sorted(REPAIR_FAMILIES - {"fallback"})
        }

    def run(self, item: SurveyItem) -> PipelineResult:
        trace = OrchestrationTrace(orchestration_enabled=True)
        router_decision = self.router.route(item)
        detected_errors = self._detected_errors_from_router(router_decision)
        trace.router_decision = router_decision.decision
        trace.taxonomy_labels = list(router_decision.taxonomy_labels)
        trace.confidence = router_decision.confidence
        trace.add_attempt(
            stage="router",
            decision=router_decision.decision,
            taxonomy_labels=router_decision.taxonomy_labels,
            confidence=router_decision.confidence,
            recommended_route=router_decision.recommended_route,
            rationale=router_decision.rationale,
        )

        route, fallback_reason = self._select_route(router_decision)
        trace.route = route
        trace.fallback_reason = fallback_reason

        if route == "manual_review":
            return self._manual_review_result(
                item=item,
                detected_errors=detected_errors,
                revised_item=_unchanged_item(
                    item,
                    note="Router requested manual review before revision.",
                ),
                trace=trace,
                reason=fallback_reason or "Router requested manual review.",
            )

        if route == "accept":
            return self._run_accept_path(
                item=item,
                router_decision=router_decision,
                detected_errors=detected_errors,
                trace=trace,
            )

        return self._run_revision_loop(
            item=item,
            router_decision=router_decision,
            detected_errors=detected_errors,
            trace=trace,
            route=route,
            fallback_reason=fallback_reason or "Router selected revision.",
            retry_count=0,
            retry_instructions=[],
        )

    def detect_only(self, item: SurveyItem) -> PipelineResult:
        trace = OrchestrationTrace(orchestration_enabled=True)
        router_decision = self.router.route(item)
        detected_errors = self._detected_errors_from_router(router_decision)
        trace.router_decision = router_decision.decision
        trace.taxonomy_labels = list(router_decision.taxonomy_labels)
        trace.confidence = router_decision.confidence
        trace.selected_agent = "router"
        trace.validation_status = "skipped"
        route, fallback_reason = self._select_route(router_decision)
        trace.route = route
        trace.fallback_reason = fallback_reason
        trace.final_status = "accepted" if route == "accept" else "single_pass"
        trace.add_attempt(
            stage="router",
            decision=router_decision.decision,
            taxonomy_labels=router_decision.taxonomy_labels,
            confidence=router_decision.confidence,
            recommended_route=router_decision.recommended_route,
            rationale=router_decision.rationale,
            evaluation_mode="detection_only",
        )
        return PipelineResult(
            item_id=item.id,
            original_item=item,
            detected_errors=detected_errors,
            revised_item=_unchanged_item(
                item,
                note="Detection-only evaluation; item left unchanged.",
            ),
            orchestration_trace=trace,
        )

    def revise_with_errors(
        self,
        item: SurveyItem,
        detected_errors: list[CheckResult],
        *,
        evaluation_mode: str = "oracle_revision",
    ) -> PipelineResult:
        if not detected_errors:
            trace = OrchestrationTrace(
                orchestration_enabled=True,
                route="accept",
                router_decision="accept",
                taxonomy_labels=[],
                confidence=1.0,
                selected_agent="gold_oracle",
                validation_status="skipped",
                final_status="accepted",
            )
            trace.add_attempt(
                stage=evaluation_mode,
                decision="accept",
                taxonomy_labels=[],
                evaluation_mode=evaluation_mode,
                rationale="No supplied labels were present; item was preserved unchanged.",
            )
            return PipelineResult(
                item_id=item.id,
                original_item=item,
                detected_errors=[],
                revised_item=_unchanged_item(
                    item,
                    note="Oracle-revision evaluation found no gold labels; item left unchanged.",
                ),
                orchestration_trace=trace,
            )

        router_decision = self._router_decision_from_detected_errors(
            detected_errors,
            evaluation_mode=evaluation_mode,
        )
        trace = OrchestrationTrace(orchestration_enabled=True)
        trace.router_decision = router_decision.decision
        trace.taxonomy_labels = list(router_decision.taxonomy_labels)
        trace.confidence = router_decision.confidence
        trace.add_attempt(
            stage=evaluation_mode,
            decision=router_decision.decision,
            taxonomy_labels=router_decision.taxonomy_labels,
            confidence=router_decision.confidence,
            recommended_route=router_decision.recommended_route,
            rationale=router_decision.rationale,
            evaluation_mode=evaluation_mode,
        )
        route, fallback_reason = self._select_route(router_decision)
        trace.route = route
        trace.fallback_reason = fallback_reason
        if route == "manual_review":
            return self._manual_review_result(
                item=item,
                detected_errors=detected_errors,
                revised_item=_unchanged_item(
                    item,
                    note="Oracle-revision routing requested manual review before revision.",
                ),
                trace=trace,
                reason=fallback_reason or "Oracle-revision routing requested manual review.",
            )
        if route == "accept":
            return self._run_accept_path(
                item=item,
                router_decision=router_decision,
                detected_errors=detected_errors,
                trace=trace,
            )
        return self._run_revision_loop(
            item=item,
            router_decision=router_decision,
            detected_errors=detected_errors,
            trace=trace,
            route=route,
            fallback_reason=fallback_reason or "Oracle-revision mode selected revision.",
            retry_count=0,
            retry_instructions=[],
        )

    def _run_accept_path(
        self,
        *,
        item: SurveyItem,
        router_decision: RouterDecision,
        detected_errors: list[CheckResult],
        trace: OrchestrationTrace,
    ) -> PipelineResult:
        revised = _unchanged_item(item, note="Router accepted item without revision.")
        trace.selected_agent = "accept"
        if not self.config.validation.enabled or not self.config.validation.validate_accept_path:
            trace.validation_status = "skipped"
            trace.add_attempt(
                stage="validator",
                status="skipped",
                retry_index=trace.retry_count,
                rationale="Validation skipped by orchestration config.",
            )
            trace.final_status = "accepted"
            return PipelineResult(
                item_id=item.id,
                original_item=item,
                detected_errors=detected_errors,
                revised_item=revised,
                orchestration_trace=trace,
            )

        validation = self.validator.validate(
            item,
            detected_errors,
            router_decision,
            revised,
            remaining_retry_budget=self.config.retry_budget,
            trace=trace,
        )
        trace.validation_status = validation.status
        trace.add_attempt(
            stage="validator",
            status=validation.status,
            retry_index=trace.retry_count,
            rationale=validation.rationale,
        )
        if validation.status == "pass":
            trace.final_status = "accepted"
            return PipelineResult(
                item_id=item.id,
                original_item=item,
                detected_errors=detected_errors,
                revised_item=revised,
                orchestration_trace=trace,
            )

        if (
            validation.status in {"retry", "failed"}
            and self.config.retry_budget > 0
            and self.config.validation.accept_failure_action == "fallback"
        ):
            trace.route = "fallback"
            trace.selected_agent = "fallback_reviser"
            trace.fallback_reason = (
                "Validator requested revision after router accepted the item."
            )
            return self._run_revision_loop(
                item=item,
                router_decision=router_decision,
                detected_errors=detected_errors,
                trace=trace,
                route="fallback",
                fallback_reason=trace.fallback_reason,
                retry_count=1,
                retry_instructions=validation.retry_instructions,
            )

        return self._manual_review_result(
            item=item,
            detected_errors=detected_errors,
            revised_item=revised,
            trace=trace,
            reason=validation.rationale or "Validator rejected the accepted item.",
        )

    def _run_revision_loop(
        self,
        *,
        item: SurveyItem,
        router_decision: RouterDecision,
        detected_errors: list[CheckResult],
        trace: OrchestrationTrace,
        route: str,
        fallback_reason: str,
        retry_count: int,
        retry_instructions: list[str],
    ) -> PipelineResult:
        current_retry_count = retry_count
        current_retry_instructions = list(retry_instructions)
        current_fallback_reason = fallback_reason
        candidate = RevisedItem(
            question=item.question,
            response_options=list(item.response_options),
            revision_notes=[],
            changed=False,
        )
        revision_plan: RevisionPlan | None = None
        current_route = route

        while True:
            trace.retry_count = current_retry_count
            remaining_retry_budget = max(self.config.retry_budget - current_retry_count, 0)
            output, revision_plan, current_route = self._revise_once(
                item=item,
                router_decision=router_decision,
                detected_errors=detected_errors,
                trace=trace,
                route=current_route,
                fallback_reason=current_fallback_reason,
                retry_count=current_retry_count,
                retry_instructions=current_retry_instructions,
            )
            candidate = output.to_revised_item()
            if not self.config.validation.enabled:
                trace.validation_status = "skipped"
                trace.add_attempt(
                    stage="validator",
                    status="skipped",
                    retry_index=current_retry_count,
                    selected_agent=trace.selected_agent,
                    rationale="Validation skipped by orchestration config.",
                )
                trace.final_status = "revised" if candidate.changed else "accepted"
                trace.route = current_route
                return PipelineResult(
                    item_id=item.id,
                    original_item=item,
                    detected_errors=detected_errors,
                    revised_item=candidate,
                    orchestration_trace=trace,
                )

            validation = self.validator.validate(
                item,
                detected_errors,
                router_decision,
                candidate,
                revision_plan=revision_plan,
                remaining_retry_budget=remaining_retry_budget,
                trace=trace,
            )
            trace.validation_status = validation.status
            trace.add_attempt(
                stage="validator",
                status=validation.status,
                retry_index=current_retry_count,
                selected_agent=trace.selected_agent,
                rationale=validation.rationale,
            )

            if validation.status == "pass":
                trace.final_status = "revised" if candidate.changed else "accepted"
                trace.route = current_route
                return PipelineResult(
                    item_id=item.id,
                    original_item=item,
                    detected_errors=detected_errors,
                    revised_item=candidate,
                    orchestration_trace=trace,
                )

            if (
                validation.status in {"retry", "failed"}
                and current_retry_count < self.config.retry_budget
            ):
                current_retry_count += 1
                current_retry_instructions = validation.retry_instructions
                if not current_retry_instructions:
                    current_retry_instructions = [validation.rationale]
                if current_route == "accept":
                    current_route = "fallback"
                    current_fallback_reason = "Validator requested a fallback retry."
                continue

            return self._manual_review_result(
                item=item,
                detected_errors=detected_errors,
                revised_item=candidate,
                trace=trace,
                reason=validation.rationale or "Validator did not pass the candidate.",
            )

    def _revise_once(
        self,
        *,
        item: SurveyItem,
        router_decision: RouterDecision,
        detected_errors: list[CheckResult],
        trace: OrchestrationTrace,
        route: str,
        fallback_reason: str,
        retry_count: int,
        retry_instructions: list[str],
    ) -> tuple[ReviserAgentOutput, RevisionPlan, str]:
        if route == "specialist" and self._sequential_enabled() and len(detected_errors) > 1:
            return self._run_sequential_specialists(
                item=item,
                router_decision=router_decision,
                detected_errors=detected_errors,
                trace=trace,
                retry_count=retry_count,
                retry_instructions=retry_instructions,
            )

        if route == "specialist":
            family = self._single_family(detected_errors)
            if family is None:
                route = "fallback"
                fallback_reason = "No single supported specialist family was available."
            else:
                agent_name = self.config.prompt_name(family)
                plan = self.planner.plan(
                    item,
                    router_decision,
                    detected_errors,
                    suggested_repair_family=family,
                    suggested_agent=agent_name,
                    retry_instructions=retry_instructions,
                    trace=trace,
                )
                trace.add_attempt(
                    stage="planner",
                    repair_family=plan.repair_family,
                    selected_agent=plan.selected_agent,
                    retry_index=retry_count,
                    rationale=plan.rationale,
                )
                allowed_families = self._families_for_errors(detected_errors)
                if plan.repair_family == "fallback" or plan.repair_family not in allowed_families:
                    route = "fallback"
                    fallback_reason = plan.fallback_reason or (
                        "Planner selected fallback or an unsupported repair family."
                    )
                else:
                    plan.selected_agent = self.config.prompt_name(plan.repair_family)
                    specialist = self.specialists[plan.repair_family]
                    trace.route = "specialist"
                    trace.selected_agent = plan.selected_agent
                    output = specialist.revise(
                        item,
                        detected_errors,
                        router_decision,
                        plan,
                        retry_instructions=retry_instructions,
                        retry_count=retry_count,
                        trace=trace,
                    )
                    trace.add_attempt(
                        stage="specialist_reviser",
                        repair_family=plan.repair_family,
                        selected_agent=plan.selected_agent,
                        retry_index=retry_count,
                        rationale=output.rationale,
                    )
                    return output, plan, "specialist"

        plan = RevisionPlan(
            repair_family="fallback",
            selected_agent="fallback_reviser",
            instructions=retry_instructions,
            fallback_reason=fallback_reason,
        )
        trace.route = "fallback"
        trace.selected_agent = "fallback_reviser"
        trace.fallback_reason = fallback_reason
        output = self.fallback_reviser.revise(
            item,
            detected_errors,
            router_decision,
            fallback_reason=fallback_reason,
            retry_instructions=retry_instructions,
            retry_count=retry_count,
            trace=trace,
        )
        trace.add_attempt(
            stage="fallback_reviser",
            selected_agent="fallback_reviser",
            retry_index=retry_count,
            fallback_reason=fallback_reason,
            rationale=output.rationale,
        )
        return output, plan, "fallback"

    def _run_sequential_specialists(
        self,
        *,
        item: SurveyItem,
        router_decision: RouterDecision,
        detected_errors: list[CheckResult],
        trace: OrchestrationTrace,
        retry_count: int,
        retry_instructions: list[str],
    ) -> tuple[ReviserAgentOutput, RevisionPlan, str]:
        current_item = item
        final_output: ReviserAgentOutput | None = None
        final_plan: RevisionPlan | None = None
        families = self._families_for_errors(detected_errors)

        for family in families:
            family_errors = [
                error
                for error in detected_errors
                if self.config.family_for_label(error.category) == family
            ]
            agent_name = self.config.prompt_name(family)
            plan = self.planner.plan(
                current_item,
                router_decision,
                family_errors,
                suggested_repair_family=family,
                suggested_agent=agent_name,
                retry_instructions=retry_instructions,
                trace=trace,
            )
            trace.add_attempt(
                stage="planner",
                repair_family=plan.repair_family,
                selected_agent=plan.selected_agent,
                retry_index=retry_count,
                rationale=plan.rationale,
            )
            if plan.repair_family == "fallback" or plan.repair_family != family:
                fallback_reason = plan.fallback_reason or (
                    "Sequential specialist planning selected fallback or an "
                    "unsupported repair family."
                )
                fallback_plan = RevisionPlan(
                    repair_family="fallback",
                    selected_agent="fallback_reviser",
                    instructions=retry_instructions,
                    fallback_reason=fallback_reason,
                )
                trace.route = "fallback"
                trace.selected_agent = "fallback_reviser"
                output = self.fallback_reviser.revise(
                    item,
                    detected_errors,
                    router_decision,
                    fallback_reason=fallback_reason,
                    retry_instructions=retry_instructions,
                    retry_count=retry_count,
                    trace=trace,
                )
                trace.add_attempt(
                    stage="fallback_reviser",
                    selected_agent="fallback_reviser",
                    retry_index=retry_count,
                    fallback_reason=fallback_reason,
                    rationale=output.rationale,
                )
                return output, fallback_plan, "fallback"
            plan.selected_agent = self.config.prompt_name(plan.repair_family)
            specialist = self.specialists[plan.repair_family]
            output = specialist.revise(
                current_item,
                family_errors,
                router_decision,
                plan,
                retry_instructions=retry_instructions,
                retry_count=retry_count,
                trace=trace,
            )
            trace.add_attempt(
                stage="specialist_reviser",
                repair_family=plan.repair_family,
                selected_agent=plan.selected_agent,
                retry_index=retry_count,
                rationale=output.rationale,
            )
            final_output = output
            final_plan = plan
            current_item = replace(
                current_item,
                question=output.question,
                response_options=list(output.response_options),
            )

        if final_output is None or final_plan is None:
            fallback_reason = "Sequential specialist planning could not produce a safe plan."
            plan = RevisionPlan(
                repair_family="fallback",
                selected_agent="fallback_reviser",
                instructions=retry_instructions,
                fallback_reason=fallback_reason,
            )
            trace.route = "fallback"
            trace.selected_agent = "fallback_reviser"
            output = self.fallback_reviser.revise(
                item,
                detected_errors,
                router_decision,
                fallback_reason=fallback_reason,
                retry_instructions=retry_instructions,
                retry_count=retry_count,
                trace=trace,
            )
            trace.add_attempt(
                stage="fallback_reviser",
                selected_agent="fallback_reviser",
                retry_index=retry_count,
                fallback_reason=fallback_reason,
                rationale=output.rationale,
            )
            return output, plan, "fallback"

        trace.route = "specialist"
        trace.selected_agent = "sequential_specialists"
        return final_output, final_plan, "specialist"

    def _select_route(self, router_decision: RouterDecision) -> tuple[str, str | None]:
        labels = [label for label in router_decision.taxonomy_labels if label]
        allowed_labels = set(self.config.taxonomy_labels)
        unknown_labels = sorted(set(labels) - allowed_labels)
        recommended_route = router_decision.recommended_route.strip().lower()

        if router_decision.confidence < self.config.confidence_threshold:
            return self._action_route(
                self.config.routing.low_confidence_action,
                "Router confidence was below the configured threshold.",
            )
        if unknown_labels:
            return self._action_route(
                self.config.routing.unknown_label_action,
                "Router returned unsupported labels: " + ", ".join(unknown_labels),
            )
        if recommended_route in {"fallback", "general_fallback", "manual_review"}:
            return self._action_route(
                self.config.routing.router_fallback_action,
                "Router recommended the general fallback route.",
            )
        if router_decision.decision == "accept":
            if labels:
                return self._action_route(
                    self.config.routing.contradictory_accept_action,
                    "Router accepted the item but also returned taxonomy labels.",
                )
            return "accept", None
        if router_decision.decision == "fallback":
            return self._action_route(
                self.config.routing.router_fallback_action,
                "Router selected fallback.",
            )
        if not labels:
            return self._action_route(
                self.config.routing.missing_taxonomy_action,
                "Router requested revision without taxonomy labels.",
            )

        families = self._families_for_labels(labels)
        if not families or "fallback" in families:
            return self._action_route(
                self.config.routing.unsupported_family_action,
                "No supported specialist family was available.",
            )
        if len(labels) > 1 and not self._sequential_enabled():
            return self._action_route(
                self.config.routing.multi_label_action,
                "Multiple taxonomy labels were routed to fallback by default.",
            )
        if len(families) > 1 and not self._sequential_enabled():
            return self._action_route(
                self.config.routing.mixed_family_action,
                "Mixed specialist families were routed to fallback by default.",
            )
        return "specialist", None

    @staticmethod
    def _action_route(action: str, reason: str) -> tuple[str, str]:
        return action, reason

    def _detected_errors_from_router(self, router_decision: RouterDecision) -> list[CheckResult]:
        detected = []
        for label in _known_taxonomy_labels(
            router_decision.taxonomy_labels,
            self.config.taxonomy_labels,
        ):
            detected.append(
                CheckResult(
                    category=label,
                    severity="medium",
                    explanation=router_decision.rationale
                    or f"Router identified the '{label}' issue.",
                    evidence=router_decision.evidence or None,
                    suggestion=router_decision.recommended_route or None,
                    checker="llm_router",
                )
            )
        return detected

    def _router_decision_from_detected_errors(
        self,
        detected_errors: list[CheckResult],
        *,
        evaluation_mode: str,
    ) -> RouterDecision:
        labels = [error.category for error in detected_errors]
        return RouterDecision(
            decision="revise",
            taxonomy_labels=labels,
            confidence=1.0,
            evidence=f"Labels supplied by {evaluation_mode} evaluation mode.",
            rationale=(
                "Use supplied labels as detected issues for revision-quality "
                "evaluation."
            ),
            recommended_route=self._recommended_route_for_labels(labels),
        )

    def _recommended_route_for_labels(self, labels: list[str]) -> str:
        families = self._families_for_labels(labels)
        if self._sequential_enabled() and len(labels) > 1:
            return "sequential_specialists"
        if families:
            return families[0]
        return "specialist"

    def _families_for_labels(self, labels: list[str]) -> list[str]:
        families: list[str] = []
        for label in labels:
            family = self.config.family_for_label(label)
            if family is None:
                continue
            if family not in families:
                families.append(family)
        return families

    def _families_for_errors(self, detected_errors: list[CheckResult]) -> list[str]:
        return self._families_for_labels([error.category for error in detected_errors])

    def _single_family(self, detected_errors: list[CheckResult]) -> str | None:
        families = self._families_for_errors(detected_errors)
        if len(families) == 1 and families[0] != "fallback":
            return families[0]
        return None

    def _sequential_enabled(self) -> bool:
        return (
            self.config.strategy == "sequential_specialists"
            and self.config.multi_label_strategy == "sequential"
        )

    def _manual_review_result(
        self,
        *,
        item: SurveyItem,
        detected_errors: list[CheckResult],
        revised_item: RevisedItem,
        trace: OrchestrationTrace,
        reason: str,
    ) -> PipelineResult:
        if trace.selected_agent is None:
            trace.selected_agent = "manual_review"
        trace.final_status = "manual_review"
        trace.manual_review_reason = reason
        trace.add_attempt(stage="manual_review", reason=reason)
        return PipelineResult(
            item_id=item.id,
            original_item=item,
            detected_errors=detected_errors,
            revised_item=revised_item,
            orchestration_trace=trace,
        )
