from __future__ import annotations

import json
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf
from rich import print_json

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.models.factory import build_model
from item_reviser.schemas import SurveyItem


@hydra.main(version_base=None, config_path="../configs", config_name="config")
def main(cfg: DictConfig) -> None:
    model = build_model(cfg.model)
    item_cfg = cfg.get("item", {})
    response_options = item_cfg.get("response_options", [])
    if isinstance(response_options, str):
        try:
            response_options = json.loads(response_options)
        except json.JSONDecodeError:
            response_options = [response_options]
    item = SurveyItem(
        id=str(item_cfg.get("id", "adhoc")),
        question=str(item_cfg.get("question", "")),
        response_options=list(response_options or []),
        target_concept=item_cfg.get("target_concept"),
    )
    if not item.question:
        item.question = "Don’t you agree that stricter environmental regulations are necessary?"
    result = ItemReviserPipeline(model=model).run(item)
    print_json(data=result.to_dict())


if __name__ == "__main__":
    main()
