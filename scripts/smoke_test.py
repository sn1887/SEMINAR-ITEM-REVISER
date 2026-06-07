from __future__ import annotations

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.schemas import SurveyItem


def main() -> None:
    item = SurveyItem(question="Don’t you agree that stricter environmental regulations are necessary?")
    result = ItemReviserPipeline().run(item)
    assert "leading_question" in result.predicted_categories()
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
