from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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
    checker: str = "rule"

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
class PipelineResult:
    item_id: str
    original_item: SurveyItem
    detected_errors: list[CheckResult]
    revised_item: RevisedItem

    def predicted_categories(self) -> list[str]:
        return sorted({error.category for error in self.detected_errors})

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "original_item": self.original_item.to_dict(),
            "detected_errors": [e.to_dict() for e in self.detected_errors],
            "predicted_categories": self.predicted_categories(),
            "revised_item": self.revised_item.to_dict(),
        }
