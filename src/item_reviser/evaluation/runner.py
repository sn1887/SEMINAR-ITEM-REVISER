from __future__ import annotations

from pathlib import Path
from typing import Any

from tqdm import tqdm

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.evaluation.dataset import load_eval_dataset
from item_reviser.evaluation.metrics import compute_detection_metrics
from item_reviser.evaluation.report import write_markdown_report
from item_reviser.io import write_json, write_jsonl
from item_reviser.models.base import BaseLLM


def run_evaluation(
    data_path: str | Path,
    output_dir: str | Path,
    model: BaseLLM | None = None,
    max_items: int | None = None,
    write_predictions: bool = True,
    write_report: bool = True,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    items = load_eval_dataset(data_path, max_items=max_items)
    pipeline = ItemReviserPipeline(model=model)

    results = []
    for item in tqdm(items, desc="Evaluating", unit="item"):
        results.append(pipeline.run(item))

    metrics = compute_detection_metrics(items, results)

    if write_predictions:
        write_jsonl(output_dir / "predictions.jsonl", [r.to_dict() for r in results])
    write_json(output_dir / "metrics.json", metrics)
    if write_report:
        write_markdown_report(output_dir / "report.md", metrics)
    return metrics
