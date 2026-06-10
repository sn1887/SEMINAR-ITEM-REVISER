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
    def from_dict(cls, data: dict[str, Any]) -> "SurveyItem":
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
    def from_dict(cls, data: dict[str, Any]) -> "RouterDecision":
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
    def from_dict(cls, data: dict[str, Any]) -> "RevisionPlan":
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
    ) -> "ReviserAgentOutput":
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
    fixes_detected_issue: bool = False
    introduces_new_issue: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidatorResult":
        return cls(
            status=_require_choice(
                str(data.get("status", "manual_review") or "manual_review"),
                VALIDATION_STATUSES,
                "validator status",
            ),
            rationale=str(data.get("rationale", "") or ""),
            retry_instructions=_as_str_list(data.get("retry_instructions")),
            preserves_construct=bool(data.get("preserves_construct", False)),
            fixes_detected_issue=bool(data.get("fixes_detected_issue", False)),
            introduces_new_issue=bool(data.get("introduces_new_issue", False)),
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
    def disabled(cls) -> "OrchestrationTrace":
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
class PipelineResult:
    item_id: str
    original_item: SurveyItem
    detected_errors: list[CheckResult]
    revised_item: RevisedItem
    orchestration_trace: OrchestrationTrace | None = None

    def predicted_categories(self) -> list[str]:
        return sorted({error.category for error in self.detected_errors})

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
        return data
