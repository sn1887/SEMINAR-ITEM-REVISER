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


def _tracking_progress_interval(cfg: DictConfig) -> int:
    value = cfg.get("tracking", {}).get("log_progress_every_items", 0)
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _configure_mlflow_tracking(cfg: DictConfig) -> Any | None:
    if not cfg.get("tracking", {}).get("enabled", False):
        return None

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
        return None

    try:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(
            cfg.get("tracking", {}).get("experiment_name", "seminar-item-reviser")
        )
    except Exception as exc:
        print(f"MLflow setup failed; continuing without tracking. Error: {exc}")
        return None
    return mlflow


def _log_mlflow_config_params(mlflow: Any, cfg: DictConfig) -> None:
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
    agent_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("agent", {}), resolve=True),
        prefix="agent",
    )
    evaluator_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("evaluator", {}), resolve=True),
        prefix="evaluator",
    )
    orchestration_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("orchestration", {}), resolve=True),
        prefix="orchestration",
    )
    tracking_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("tracking", {}), resolve=True),
        prefix="tracking",
    )
    prompt_cfg = _flatten_params(
        OmegaConf.to_container(cfg.get("prompt", {}), resolve=True),
        prefix="prompt",
    )

    mlflow.log_param("seed", int(cfg.seed))
    mlflow.log_params(model_cfg)
    mlflow.log_params(data_cfg)
    mlflow.log_params(experiment_cfg)
    mlflow.log_params(agent_cfg)
    mlflow.log_params(evaluator_cfg)
    mlflow.log_params(orchestration_cfg)
    mlflow.log_params(tracking_cfg)
    mlflow.log_params(prompt_cfg)


def _log_mlflow_final_outputs(
    mlflow: Any,
    metrics: dict[str, Any],
    output_dir: Path,
    *,
    log_metrics: bool,
) -> None:
    dataset_cfg = _flatten_params(metrics.get("dataset", {}), prefix="dataset")
    mlflow.log_params(dataset_cfg)
    if log_metrics:
        mlflow.log_metrics(
            _flatten_scalars(metrics),
            step=int(metrics.get("num_items", 0)),
        )
    if output_dir.exists():
        mlflow.log_artifacts(str(output_dir), artifact_path="outputs")


@hydra.main(version_base=None, config_path="../configs", config_name="config")
def main(cfg: DictConfig) -> None:
    set_seed(int(cfg.seed))
    model = build_model(cfg.model)
    max_items = cfg.experiment.get("max_items")
    mlflow = _configure_mlflow_tracking(cfg)

    progress_logged_final = False
    if mlflow is None:
        metrics = run_evaluation(
            data_path=cfg.data.path,
            output_dir=cfg.paths.output_dir,
            model=model,
            prompt_config=cfg.prompt,
            agent_config=cfg.get("agent"),
            orchestration_config=cfg.get("orchestration"),
            max_items=max_items,
            write_predictions=bool(cfg.experiment.get("write_predictions", True)),
            write_report=bool(cfg.experiment.get("write_report", True)),
            use_severity_weighted_scoring=bool(
                cfg.experiment.get("severity_weighted_scoring", False)
            ),
            continue_on_item_error=bool(
                cfg.evaluator.get("continue_on_item_error", True)
            ),
            write_predictions_incrementally=bool(
                cfg.evaluator.get("write_predictions_incrementally", True)
            ),
            include_error_traceback=bool(
                cfg.evaluator.get("include_error_traceback", True)
            ),
        )
    else:
        progress_interval = _tracking_progress_interval(cfg)
        progress_logging_failed = False

        def _log_progress(completed: int, total: int, progress_metrics: dict[str, Any]) -> None:
            nonlocal progress_logged_final, progress_logging_failed
            if progress_logging_failed:
                return
            try:
                mlflow.log_metrics(_flatten_scalars(progress_metrics), step=completed)
                progress_logged_final = completed == total
            except Exception as exc:
                progress_logging_failed = True
                print(f"MLflow progress logging failed; continuing evaluation. Error: {exc}")

        run_name = cfg.get("tracking", {}).get("run_name")
        try:
            active_run = mlflow.start_run(run_name=run_name)
        except Exception as exc:
            print(f"MLflow run start failed; continuing without tracking. Error: {exc}")
            metrics = run_evaluation(
                data_path=cfg.data.path,
                output_dir=cfg.paths.output_dir,
                model=model,
                prompt_config=cfg.prompt,
                agent_config=cfg.get("agent"),
                orchestration_config=cfg.get("orchestration"),
                max_items=max_items,
                write_predictions=bool(cfg.experiment.get("write_predictions", True)),
                write_report=bool(cfg.experiment.get("write_report", True)),
                use_severity_weighted_scoring=bool(
                    cfg.experiment.get("severity_weighted_scoring", False)
                ),
                continue_on_item_error=bool(
                    cfg.evaluator.get("continue_on_item_error", True)
                ),
                write_predictions_incrementally=bool(
                    cfg.evaluator.get("write_predictions_incrementally", True)
                ),
                include_error_traceback=bool(
                    cfg.evaluator.get("include_error_traceback", True)
                ),
            )
        else:
            with active_run:
                try:
                    _log_mlflow_config_params(mlflow, cfg)
                except Exception as exc:
                    print(f"MLflow parameter logging failed; continuing evaluation. Error: {exc}")

                metrics = run_evaluation(
                    data_path=cfg.data.path,
                    output_dir=cfg.paths.output_dir,
                    model=model,
                    prompt_config=cfg.prompt,
                    agent_config=cfg.get("agent"),
                    orchestration_config=cfg.get("orchestration"),
                    max_items=max_items,
                    write_predictions=bool(cfg.experiment.get("write_predictions", True)),
                    write_report=bool(cfg.experiment.get("write_report", True)),
                    use_severity_weighted_scoring=bool(
                        cfg.experiment.get("severity_weighted_scoring", False)
                    ),
                    continue_on_item_error=bool(
                        cfg.evaluator.get("continue_on_item_error", True)
                    ),
                    write_predictions_incrementally=bool(
                        cfg.evaluator.get("write_predictions_incrementally", True)
                    ),
                    include_error_traceback=bool(
                        cfg.evaluator.get("include_error_traceback", True)
                    ),
                    progress_callback=_log_progress if progress_interval > 0 else None,
                    progress_interval=progress_interval,
                )
                try:
                    _log_mlflow_final_outputs(
                        mlflow,
                        metrics,
                        Path(cfg.paths.output_dir),
                        log_metrics=not progress_logged_final,
                    )
                except Exception as exc:
                    print(f"MLflow final logging failed after evaluation. Error: {exc}")
    print_json(data=metrics)


if __name__ == "__main__":
    main()
