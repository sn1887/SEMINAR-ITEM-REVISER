from __future__ import annotations

from pathlib import Path

from item_reviser.io import load_items
from item_reviser.schemas import SurveyItem


def load_eval_dataset(path: str | Path, max_items: int | None = None) -> list[SurveyItem]:
    items = load_items(path)
    if max_items is not None:
        return items[:max_items]
    return items
