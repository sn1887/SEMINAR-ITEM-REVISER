from __future__ import annotations

from dataclasses import dataclass

from item_reviser.agents.base import BaseAgent


@dataclass
class ConceptMapping:
    concept: str
    concept_type: str
    indicators: list[str]


class ConceptMapperAgent(BaseAgent):
    """Stub for earlier seminar pipeline component."""

    def map_concept(self, concept: str) -> ConceptMapping:
        return ConceptMapping(concept=concept, concept_type="unknown", indicators=[concept])
