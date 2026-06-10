from __future__ import annotations

from pathlib import Path
from typing import Any

from tqdm import tqdm

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.constants import CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY
from item_reviser.evaluation.dataset import load_eval_dataset_with_metadata
from item_reviser.evaluation.metrics import compute_detection_metrics
from item_reviser.evaluation.report import write_markdown_report
from item_reviser.io import write_json, write_jsonl
from item_reviser.models.base import BaseLLM


def _summarize_orchestration(results: list[Any]) -> dict[str, Any]:
    traces = [result.orchestration_trace for result in results if result.orchestration_trace]
    if not traces:
        return {"enabled": False}

    def _count(field_name: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for trace in traces:
            value = getattr(trace, field_name)
            key = str(value) if value is not None else "none"
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    return {
        "enabled": any(trace.orchestration_enabled for trace in traces),
        "items_with_trace": len(traces),
        "routes": _count("route"),
        "router_decisions": _count("router_decision"),
        "selected_agents": _count("selected_agent"),
        "validation_statuses": _count("validation_status"),
        "final_statuses": _count("final_status"),
        "mean_retry_count": sum(trace.retry_count for trace in traces) / len(traces),
    }


def run_evaluation(
    data_path: str | Path,
    output_dir: str | Path,
    model: BaseLLM,
    prompt_config: object,
    orchestration_config: object | None = None,
    max_items: int | None = None,
    write_predictions: bool = True,
    write_report: bool = True,
    use_severity_weighted_scoring: bool = False,
) -> dict[str, Any]:
    if model is None:
        raise ValueError("run_evaluation requires an LLM model.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    items, dataset_metadata = load_eval_dataset_with_metadata(data_path, max_items=max_items)
    pipeline = ItemReviserPipeline(
        model=model,
        prompt_config=prompt_config,
        orchestration_config=orchestration_config,
    )

    results = []
    for item in tqdm(items, desc="Evaluating", unit="item"):
        results.append(pipeline.run(item))

    category_weights = (
        CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY
        if use_severity_weighted_scoring
        else None
    )
    metrics = compute_detection_metrics(
        items,
        results,
        use_severity_weighting=use_severity_weighted_scoring,
        category_weights=category_weights,
    )
    metrics["dataset"] = dataset_metadata.to_dict()
    metrics["orchestration"] = _summarize_orchestration(results)

    if write_predictions:
        write_jsonl(output_dir / "predictions.jsonl", [r.to_dict() for r in results])
    write_json(output_dir / "dataset_metadata.json", dataset_metadata.to_dict())
    write_json(output_dir / "metrics.json", metrics)
    if write_report:
        write_markdown_report(output_dir / "report.md", metrics)
    return metrics
