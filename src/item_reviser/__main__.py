from __future__ import annotations

import os
from pathlib import Path

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.models.factory import build_model
from item_reviser.schemas import SurveyItem


def main() -> None:
    model_path = os.getenv("MODEL_PATH", "").strip()
    if not model_path:
        raise SystemExit("Set MODEL_PATH to a local Hugging Face model path before running.")
    model = build_model({"backend": "hf_local", "model_path": model_path})
    prompt_dir = Path(os.getenv("PROMPT_DIR", "prompts"))
    prompt_config = {
        "quality_checker": {
            "template_path": str(prompt_dir / "agents" / "quality_checker.md"),
        },
        "item_reviser": {
            "template_path": str(prompt_dir / "agents" / "item_reviser.md"),
        },
    }
    item = SurveyItem(question="Don’t you agree that stricter environmental regulations are necessary?")
    result = ItemReviserPipeline(model=model, prompt_config=prompt_config).run(item)
    print(result.to_dict())


if __name__ == "__main__":
    main()
