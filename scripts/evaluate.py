from __future__ import annotations

import hydra
from omegaconf import DictConfig
from rich import print_json

from item_reviser.evaluation.runner import run_evaluation
from item_reviser.models.factory import build_model
from item_reviser.utils import set_seed


@hydra.main(version_base=None, config_path="../configs", config_name="config")
def main(cfg: DictConfig) -> None:
    set_seed(int(cfg.seed))
    model = build_model(cfg.model)
    max_items = cfg.experiment.get("max_items")
    metrics = run_evaluation(
        data_path=cfg.data.path,
        output_dir=cfg.paths.output_dir,
        model=model,
        max_items=max_items,
        write_predictions=bool(cfg.experiment.get("write_predictions", True)),
        write_report=bool(cfg.experiment.get("write_report", True)),
    )
    print_json(data=metrics)


if __name__ == "__main__":
    main()
