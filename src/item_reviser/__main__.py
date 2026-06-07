from __future__ import annotations

from item_reviser.schemas import SurveyItem
from item_reviser.agents.pipeline import ItemReviserPipeline


def main() -> None:
    item = SurveyItem(question="Don’t you agree that stricter environmental regulations are necessary?")
    result = ItemReviserPipeline().run(item)
    print(result.to_dict())


if __name__ == "__main__":
    main()
