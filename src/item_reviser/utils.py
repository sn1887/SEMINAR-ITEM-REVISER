from __future__ import annotations

import random
from collections.abc import Iterable
from typing import TypeVar

import numpy as np

T = TypeVar("T")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def unique_preserve_order(items: Iterable[T]) -> list[T]:
    seen: set[T] = set()
    out: list[T] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())
