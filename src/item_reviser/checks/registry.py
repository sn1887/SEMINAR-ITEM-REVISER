from __future__ import annotations

from item_reviser.checks.scale import ScaleChecker
from item_reviser.checks.wording import WordingChecker
from item_reviser.schemas import CheckResult, SurveyItem
from item_reviser.utils import unique_preserve_order


def default_checkers() -> list[object]:
    return [WordingChecker(), ScaleChecker()]


def run_all_checks(item: SurveyItem) -> list[CheckResult]:
    results: list[CheckResult] = []
    for checker in default_checkers():
        results.extend(checker.check(item))

    # Deduplicate by category; keep first explanation.
    seen: set[str] = set()
    deduped: list[CheckResult] = []
    for result in results:
        if result.category in seen:
            continue
        seen.add(result.category)
        deduped.append(result)

    # Stable category order if possible.
    order = unique_preserve_order([r.category for r in deduped])
    return sorted(deduped, key=lambda r: order.index(r.category))
