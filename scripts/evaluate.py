from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import hydra  # noqa: E402
from omegaconf import DictConfig, OmegaConf  # noqa: E402
from rich import print_json  # noqa: E402

from item_reviser.evaluation.runner import run_evaluation  # noqa: E402
from item_reviser.models.factory import build_model  # noqa: E402
from item_reviser.utils import set_seed  # noqa: E402


def _flatten_scalars(
    data: Any, prefix: str = "", separator: str = "."
) -> dict[str, float]:
    flat: dict[str, float] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f"{prefix}{separator}{key}" if prefix else str(key)
            flat.update(_flatten_scalars(value, next_prefix, separator))
        return flat

    if isinstance(data, bool):
        return {prefix: float(data)}

    if isinstance(data, (int, float)):
        return {prefix: float(data)}

    return flat


def _flatten_params(
    data: Any, prefix: str = "", separator: str = "."
) -> dict[str, str]:
    flat: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f"{prefix}{separator}{key}" if prefix else str(key)
            flat.update(_flatten_params(value, next_prefix, separator))
        return flat

    if isinstance(data, (str, int, float, bool)):
        return {prefix: str(data)}

    if isinstance(data, (list, tuple, set)):
        return {prefix: json.dumps(list(data), sort_keys=True)}

    if data is None:
        return {prefix: "null"}

    # Keep params concise and stable for MLflow; skip complex nested objects.
    return {}


def _run_mlflow_tracking(cfg: DictConfig, metrics: dict[str, Any], output_dir: Path) -> None:
    if not cfg.get("tracking", {}).get("enabled", False):
        return

    tracking_uri = cfg.get("tracking", {}).get("tracking_uri")
    if not tracking_uri:
        tracking_uri = os.getenv(
            "MLFLOW_TRACKING_URI",
            f"file://{Path(cfg.paths.root).resolve() / 'mlruns'}",
        )

    tracking_uri = str(tracking_uri)
    if tracking_uri.startswith("file://") or "://" not in tracking_uri:
        os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
        tracking_path = (
            Path(tracking_uri.removeprefix("file://"))
            if tracking_uri.startswith("file://")
            else Path(tracking_uri)
        )
        tracking_path.mkdir(parents=True, exist_ok=True)

    try:
        import mlflow
    except Exception:
        print(
            "MLflow is enabled but not installed. Install with "
            "`pip install -e .[mlflow]` or `pip install -e .[hf]`."
        )
        return

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(cfg.get("tracking", {}).get("experiment_name", "seminar-item-reviser"))

    model_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("model", {}), resolve=True),
        prefix="model",
    )
    data_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("data", {}), resolve=True),
        prefix="data",
    )
    experiment_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("experiment", {}), resolve=True),
        prefix="experiment",
    )
    tracking_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("tracking", {}), resolve=True),
        prefix="tracking",
    )
    prompt_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("prompt", {}), resolve=True),
        prefix="prompt",
    )
    dataset_cfg = _flatten_params(metrics.get("dataset", {}), prefix="dataset")

    run_name = cfg.get("tracking", {}).get("run_name")
    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("seed", int(cfg.seed))
        mlflow.log_params(model_cfg)
        mlflow.log_params(data_cfg)
        mlflow.log_params(experiment_cfg)
        mlflow.log_params(tracking_cfg)
        mlflow.log_params(prompt_cfg)
        mlflow.log_params(dataset_cfg)
        mlflow.log_metrics(_flatten_scalars(metrics))
        if output_dir.exists():
            mlflow.log_artifacts(str(output_dir), artifact_path="outputs")


@hydra.main(version_base=None, config_path="../configs", config_name="config")
def main(cfg: DictConfig) -> None:
    set_seed(int(cfg.seed))
    model = build_model(cfg.model)
    max_items = cfg.experiment.get("max_items")
    metrics = run_evaluation(
        data_path=cfg.data.path,
        output_dir=cfg.paths.output_dir,
        model=model,
        prompt_config=cfg.prompt,
        max_items=max_items,
        write_predictions=bool(cfg.experiment.get("write_predictions", True)),
        write_report=bool(cfg.experiment.get("write_report", True)),
        use_severity_weighted_scoring=bool(
            cfg.experiment.get("severity_weighted_scoring", False)
        ),
    )
    _run_mlflow_tracking(cfg=cfg, metrics=metrics, output_dir=Path(cfg.paths.output_dir))
    print_json(data=metrics)


if __name__ == "__main__":
    main()
