from __future__ import annotations

import os

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.models.factory import build_model
from item_reviser.schemas import SurveyItem


def main() -> None:
    model_path = os.getenv("MODEL_PATH", "").strip()
    if not model_path:
        raise SystemExit("Set MODEL_PATH to a local Hugging Face model path before running.")
    model = build_model({"backend": "hf_local", "model_path": model_path})
    item = SurveyItem(question="Don’t you agree that stricter environmental regulations are necessary?")
    result = ItemReviserPipeline(model=model).run(item)
    print(result.to_dict())


if __name__ == "__main__":
    main()
