from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

ROUTER_DECISIONS = {"accept", "revise", "fallback"}
ORCHESTRATION_ROUTES = {
    "single_pass",
    "accept",
    "specialist",
    "fallback",
    "manual_review",
}
REPAIR_FAMILIES = {
    "wording_clarity",
    "response_options_scale",
    "construct_alignment",
    "bias_sensitivity",
    "questionnaire_format",
    "fallback",
}
VALIDATION_STATUSES = {"pass", "retry", "manual_review", "failed"}
FINAL_STATUSES = {
    "single_pass",
    "accepted",
    "revised",
    "manual_review",
    "failed",
}


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return [str(value)]


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_confidence(value: Any) -> float:
    confidence = _coerce_float(value)
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError("router confidence must be between 0 and 1.")
    return confidence


def _require_choice(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {choices}")
    return value


@dataclass
class SurveyItem:
    id: str = "adhoc"
    question: str = ""
    response_options: list[str] = field(default_factory=list)
    target_concept: str | None = None
    topic: str | None = None
    known_errors: list[str] = field(default_factory=list)
    is_flawed: bool | None = None
    expected_revision: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SurveyItem:
        expected_revision = data.get("expected_revision", {})
        if not isinstance(expected_revision, dict):
            expected_revision = {"question": "", "response_options": []}
        return cls(
            id=str(data.get("id", "adhoc")),
            question=str(data.get("question", "")),
            response_options=list(data.get("response_options") or []),
            target_concept=data.get("target_concept"),
            topic=data.get("topic"),
            known_errors=list(data.get("known_errors") or []),
            is_flawed=data.get("is_flawed"),
            expected_revision=expected_revision,
            metadata=dict(data.get("metadata") or {}),
        )

    def needs_manual_review(self) -> bool:
        value = self.metadata.get("needs_manual_review", False)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return bool(value)

    def model_input(self) -> dict[str, Any]:
        """Return the only item fields allowed in model-facing prompts."""
        return {
            "question": self.question,
            "response_options": list(self.response_options),
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    category: str
    severity: str
    explanation: str
    evidence: str | None = None
    suggestion: str | None = None
    checker: str = "llm"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RevisedItem:
    question: str
    response_options: list[str] = field(default_factory=list)
    revision_notes: list[str] = field(default_factory=list)
    changed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RouterDecision:
    decision: str
    taxonomy_labels: list[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: str = ""
    rationale: str = ""
    recommended_route: str = "fallback"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouterDecision:
        decision = _require_choice(
            str(data.get("decision", "fallback") or "fallback"),
            ROUTER_DECISIONS,
            "router decision",
        )
        return cls(
            decision=decision,
            taxonomy_labels=_as_str_list(data.get("taxonomy_labels")),
            confidence=_coerce_confidence(data.get("confidence")),
            evidence=str(data.get("evidence", "") or ""),
            rationale=str(data.get("rationale", "") or ""),
            recommended_route=str(data.get("recommended_route", "fallback") or "fallback"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RevisionPlan:
    repair_family: str = "fallback"
    selected_agent: str = "fallback_reviser"
    instructions: list[str] = field(default_factory=list)
    fallback_reason: str | None = None
    rationale: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RevisionPlan:
        return cls(
            repair_family=_require_choice(
                str(data.get("repair_family", "fallback") or "fallback"),
                REPAIR_FAMILIES,
                "repair family",
            ),
            selected_agent=str(
                data.get("selected_agent", "fallback_reviser") or "fallback_reviser"
            ),
            instructions=_as_str_list(data.get("instructions")),
            fallback_reason=(
                str(data.get("fallback_reason"))
                if data.get("fallback_reason") is not None
                else None
            ),
            rationale=str(data.get("rationale", "") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviserAgentOutput:
    question: str
    response_options: list[str] = field(default_factory=list)
    revision_notes: list[str] = field(default_factory=list)
    changed: bool = True
    agent_name: str = ""
    rationale: str = ""

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        original_item: SurveyItem,
        agent_name: str,
    ) -> ReviserAgentOutput:
        response_options = data.get("response_options", original_item.response_options)
        if not isinstance(response_options, list):
            response_options = original_item.response_options
        revision_notes = data.get("revision_notes", ["LLM revision provided"])
        return cls(
            question=str(data.get("question", original_item.question) or original_item.question),
            response_options=[str(option) for option in response_options],
            revision_notes=_as_str_list(revision_notes),
            changed=bool(data.get("changed", True)),
            agent_name=str(data.get("agent_name", agent_name) or agent_name),
            rationale=str(data.get("rationale", "") or ""),
        )

    def to_revised_item(self) -> RevisedItem:
        return RevisedItem(
            question=self.question,
            response_options=self.response_options,
            revision_notes=self.revision_notes,
            changed=self.changed,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatorResult:
    status: str = "manual_review"
    rationale: str = ""
    retry_instructions: list[str] = field(default_factory=list)
    preserves_construct: bool = False
    fixes_detected_issue: bool | None = None
    introduces_new_issue: bool = False

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        has_detected_issues: bool | None = None,
    ) -> ValidatorResult:
        result = cls(
            status=_require_choice(
                str(data.get("status", "manual_review") or "manual_review"),
                VALIDATION_STATUSES,
                "validator status",
            ),
            rationale=str(data.get("rationale", "") or ""),
            retry_instructions=_as_str_list(data.get("retry_instructions")),
            preserves_construct=bool(data.get("preserves_construct", False)),
            fixes_detected_issue=(
                None
                if data.get("fixes_detected_issue") is None
                else bool(data["fixes_detected_issue"])
            ),
            introduces_new_issue=bool(data.get("introduces_new_issue", False)),
        )
        return result.enforce_pass_invariants(
            has_detected_issues=has_detected_issues
        )

    def enforce_pass_invariants(
        self,
        *,
        has_detected_issues: bool | None = None,
    ) -> ValidatorResult:
        """Downgrade contradictory pass outputs before orchestration trusts them."""

        if self.status != "pass":
            return self

        violations: list[str] = []
        if not self.preserves_construct:
            violations.append("preserves_construct must be true")
        if self.introduces_new_issue:
            violations.append("introduces_new_issue must be false")
        if self.retry_instructions:
            violations.append("retry_instructions must be empty")
        if has_detected_issues is True and self.fixes_detected_issue is not True:
            violations.append("fixes_detected_issue must be true with detected issues")
        elif has_detected_issues is False and self.fixes_detected_issue is not None:
            violations.append("fixes_detected_issue must be null without detected issues")
        elif has_detected_issues is None and self.fixes_detected_issue is False:
            violations.append("fixes_detected_issue must not be false for pass")

        if not violations:
            return self

        status = "retry" if self.retry_instructions else "manual_review"
        rationale = self.rationale.strip()
        suffix = "Contradictory validator pass downgraded: " + "; ".join(violations) + "."
        return ValidatorResult(
            status=status,
            rationale=f"{rationale} {suffix}".strip(),
            retry_instructions=list(self.retry_instructions) if status == "retry" else [],
            preserves_construct=self.preserves_construct,
            fixes_detected_issue=self.fixes_detected_issue,
            introduces_new_issue=self.introduces_new_issue,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrchestrationTrace:
    orchestration_enabled: bool = False
    route: str = "single_pass"
    router_decision: str | None = None
    taxonomy_labels: list[str] = field(default_factory=list)
    confidence: float | None = None
    selected_agent: str | None = None
    retry_count: int = 0
    validation_status: str | None = None
    final_status: str = "single_pass"
    fallback_reason: str | None = None
    manual_review_reason: str | None = None
    attempts: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def disabled(cls) -> OrchestrationTrace:
        return cls()

    def add_attempt(self, **values: Any) -> None:
        self.attempts.append(
            {
                key: value
                for key, value in values.items()
                if value is not None
            }
        )

    def to_evaluation_fields(self) -> dict[str, Any]:
        return {
            "orchestration_enabled": self.orchestration_enabled,
            "route": self.route,
            "router_decision": self.router_decision,
            "taxonomy_labels": list(self.taxonomy_labels),
            "confidence": self.confidence,
            "selected_agent": self.selected_agent,
            "retry_count": self.retry_count,
            "validation_status": self.validation_status,
            "final_status": self.final_status,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineError:
    error_type: str
    message: str
    stage: str = "pipeline"
    traceback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    item_id: str
    original_item: SurveyItem
    detected_errors: list[CheckResult]
    revised_item: RevisedItem
    orchestration_trace: OrchestrationTrace | None = None
    error: PipelineError | None = None

    def predicted_categories(self) -> list[str]:
        return sorted({error.category for error in self.detected_errors})

    def failed(self) -> bool:
        return self.error is not None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "item_id": self.item_id,
            "original_item": self.original_item.to_dict(),
            "detected_errors": [e.to_dict() for e in self.detected_errors],
            "predicted_categories": self.predicted_categories(),
            "revised_item": self.revised_item.to_dict(),
        }
        if self.orchestration_trace is not None:
            data["orchestration_trace"] = self.orchestration_trace.to_dict()
            data["orchestration"] = self.orchestration_trace.to_evaluation_fields()
        if self.error is not None:
            data["error"] = self.error.to_dict()
        return data

    def to_blind_dict(self, *, opaque_id: str) -> dict[str, Any]:
        data = {
            "item_id": opaque_id,
            "original_item": self.original_item.model_input(),
            "detected_errors": [e.to_dict() for e in self.detected_errors],
            "predicted_categories": self.predicted_categories(),
            "revised_item": self.revised_item.to_dict(),
        }
        if self.orchestration_trace is not None:
            data["orchestration_trace"] = self.orchestration_trace.to_dict()
            data["orchestration"] = self.orchestration_trace.to_evaluation_fields()
        if self.error is not None:
            data["error"] = self.error.to_dict()
        return data
