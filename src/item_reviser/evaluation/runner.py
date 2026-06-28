from __future__ import annotations

import json
import traceback
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tqdm import tqdm

from item_reviser.agents.pipeline import ItemReviserPipeline
from item_reviser.constants import CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY
from item_reviser.evaluation.dataset import (
    DEFAULT_SAMPLING_SEED,
    load_eval_dataset_with_metadata,
)
from item_reviser.evaluation.metrics import compute_detection_metrics
from item_reviser.evaluation.report import write_markdown_report
from item_reviser.io import write_json, write_jsonl
from item_reviser.models.base import BaseLLM
from item_reviser.schemas import (
    OrchestrationTrace,
    PipelineError,
    PipelineResult,
    RevisedItem,
    SurveyItem,
)

ProgressCallback = Callable[[int, int, dict[str, Any]], None]


def _opaque_eval_id(index: int) -> str:
    return f"eval-{index:06d}"


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


def _artifact_item_id(result: PipelineResult, index: int, *, include_gold: bool) -> str:
    return result.item_id if include_gold else _opaque_eval_id(index)


def _summarize_failures(
    results: list[PipelineResult],
    *,
    include_gold: bool,
) -> dict[str, Any]:
    failed_results = [result for result in results if result.error is not None]
    failure_types = Counter(result.error.error_type for result in failed_results if result.error)
    failure_stages = Counter(result.error.stage for result in failed_results if result.error)
    failure_items: list[dict[str, Any]] = []
    for index, result in enumerate(results, start=1):
        if result.error is None:
            continue
        item_id = _artifact_item_id(result, index, include_gold=include_gold)
        message = result.error.message
        if not include_gold:
            message = _replace_source_id(
                message,
                source_id=result.item_id,
                opaque_id=item_id,
            )
        failure_items.append(
            {
                "item_id": item_id,
                "error_type": result.error.error_type,
                "stage": result.error.stage,
                "message": message,
            }
        )
    return {
        "count": len(failed_results),
        "rate": len(failed_results) / len(results) if results else 0.0,
        "types": dict(sorted(failure_types.items())),
        "stages": dict(sorted(failure_stages.items())),
        "items": failure_items,
    }


def _config_get(config: object | None, key: str, default: Any = None) -> Any:
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(key, default)
    if hasattr(config, "get"):
        return config.get(key, default)  # type: ignore[call-arg]
    return getattr(config, key, default)


def _orchestration_enabled(orchestration_config: object | None) -> bool:
    return bool(_config_get(orchestration_config, "enabled", False))


def _failure_result(
    item: SurveyItem,
    exc: Exception,
    *,
    orchestration_enabled: bool,
    include_traceback: bool,
) -> PipelineResult:
    trace = None
    if orchestration_enabled:
        trace = OrchestrationTrace(
            orchestration_enabled=True,
            route="manual_review",
            selected_agent="evaluation_runner",
            validation_status="failed",
            final_status="failed",
            manual_review_reason=(
                "Evaluation failed after the model produced an invalid or unusable "
                "response."
            ),
        )
        trace.add_attempt(
            stage="evaluation_runner",
            selected_agent="evaluation_runner",
            rationale=f"{type(exc).__name__}: {exc}",
        )

    return PipelineResult(
        item_id=item.id,
        original_item=item,
        detected_errors=[],
        revised_item=RevisedItem(
            question=item.question,
            response_options=list(item.response_options),
            revision_notes=[
                "Evaluation failed for this item; original item left unchanged."
            ],
            changed=False,
        ),
        orchestration_trace=trace,
        error=PipelineError(
            error_type=type(exc).__name__,
            message=str(exc),
            stage="pipeline.run",
            traceback=traceback.format_exc() if include_traceback else None,
        ),
    )


def _replace_source_id(value: Any, *, source_id: str, opaque_id: str) -> Any:
    if not source_id:
        return value
    if isinstance(value, str):
        return value.replace(source_id, opaque_id)
    if isinstance(value, list):
        return [
            _replace_source_id(item, source_id=source_id, opaque_id=opaque_id)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            str(key): _replace_source_id(
                item,
                source_id=source_id,
                opaque_id=opaque_id,
            )
            for key, item in value.items()
        }
    return value


def _blinded_original_item(item: SurveyItem, opaque_id: str) -> dict[str, Any]:
    _ = opaque_id
    return item.model_input()


def _prediction_record(
    result: PipelineResult,
    *,
    opaque_id: str,
    include_gold: bool,
) -> dict[str, Any]:
    if include_gold:
        return result.to_dict()

    data: dict[str, Any] = {
        "item_id": opaque_id,
        "original_item": _blinded_original_item(result.original_item, opaque_id),
        "detected_errors": [error.to_dict() for error in result.detected_errors],
        "predicted_categories": result.predicted_categories(),
        "revised_item": result.revised_item.to_dict(),
    }
    if result.orchestration_trace is not None:
        data["orchestration_trace"] = result.orchestration_trace.to_dict()
        data["orchestration"] = result.orchestration_trace.to_evaluation_fields()
    if result.error is not None:
        data["error"] = result.error.to_dict()
    return _replace_source_id(
        data,
        source_id=result.item_id,
        opaque_id=opaque_id,
    )


def _needs_manual_review_export(result: PipelineResult) -> bool:
    if result.failed():
        return True
    trace = result.orchestration_trace
    return trace is not None and trace.final_status == "manual_review"


def _manual_review_record(result: PipelineResult, *, opaque_id: str) -> dict[str, Any]:
    record = _prediction_record(result, opaque_id=opaque_id, include_gold=False)
    trace = result.orchestration_trace
    review_reason = None
    if result.error is not None:
        review_reason = result.error.message
    elif trace is not None:
        review_reason = trace.manual_review_reason
    record["manual_review"] = {
        "required": True,
        "reason": _replace_source_id(
            review_reason or "Pipeline flagged this item for manual review.",
            source_id=result.item_id,
            opaque_id=opaque_id,
        ),
    }
    return record


def _write_jsonl_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()


def _compute_metrics(
    items: list[SurveyItem],
    results: list[PipelineResult],
    *,
    dataset_metadata: Any,
    use_severity_weighted_scoring: bool,
    include_gold: bool,
) -> dict[str, Any]:
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
    failures = _summarize_failures(results, include_gold=include_gold)
    metrics["failed_items"] = failures["count"]
    metrics["successful_items"] = len(results) - failures["count"]
    metrics["failure_rate"] = failures["rate"]
    metrics["failures"] = failures
    metrics["artifacts"] = {
        "prediction_id_mode": "source" if include_gold else "opaque",
        "gold_in_prediction_rows": bool(include_gold),
        "prediction_id_example": "source item id" if include_gold else _opaque_eval_id(1),
    }
    return metrics


def run_evaluation(
    data_path: str | Path,
    output_dir: str | Path,
    model: BaseLLM,
    prompt_config: object,
    agent_config: object | None = None,
    orchestration_config: object | None = None,
    max_items: int | None = None,
    write_predictions: bool = True,
    write_report: bool = True,
    use_severity_weighted_scoring: bool = False,
    progress_callback: ProgressCallback | None = None,
    progress_interval: int = 0,
    continue_on_item_error: bool = True,
    write_predictions_incrementally: bool = True,
    include_error_traceback: bool = True,
    include_gold: bool = False,
    sampling_seed: int = DEFAULT_SAMPLING_SEED,
) -> dict[str, Any]:
    if model is None:
        raise ValueError("run_evaluation requires an LLM model.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    items, dataset_metadata = load_eval_dataset_with_metadata(
        data_path,
        max_items=max_items,
        sampling_seed=sampling_seed,
    )
    pipeline = ItemReviserPipeline(
        model=model,
        prompt_config=prompt_config,
        agent_config=agent_config,
        orchestration_config=orchestration_config,
    )

    write_json(output_dir / "dataset_metadata.json", dataset_metadata.to_dict())

    results: list[PipelineResult] = []
    total_items = len(items)
    predictions_path = output_dir / "predictions.jsonl"
    manual_review_path = output_dir / "manual_review.jsonl"
    if write_predictions and write_predictions_incrementally:
        predictions_path.parent.mkdir(parents=True, exist_ok=True)
        predictions_path.write_text("", encoding="utf-8")
        manual_review_path.write_text("", encoding="utf-8")

    for index, item in enumerate(tqdm(items, desc="Evaluating", unit="item"), start=1):
        opaque_id = _opaque_eval_id(index)
        try:
            result = pipeline.run(item)
        except Exception as exc:
            if not continue_on_item_error:
                raise
            result = _failure_result(
                item,
                exc,
                orchestration_enabled=_orchestration_enabled(orchestration_config),
                include_traceback=include_error_traceback,
            )
            print(
                f"Item {item.id} failed with {type(exc).__name__}; "
                "recorded failure and continuing evaluation."
            )
        results.append(result)

        if write_predictions and write_predictions_incrementally:
            _write_jsonl_record(
                predictions_path,
                _prediction_record(
                    result,
                    opaque_id=opaque_id,
                    include_gold=include_gold,
                ),
            )
            if _needs_manual_review_export(result):
                _write_jsonl_record(
                    manual_review_path,
                    _manual_review_record(result, opaque_id=opaque_id),
                )

        should_report_progress = (
            progress_callback is not None
            and progress_interval > 0
            and (index % progress_interval == 0 or index == total_items)
        )
        if should_report_progress:
            progress_metrics = _compute_metrics(
                items[:index],
                results,
                dataset_metadata=dataset_metadata,
                use_severity_weighted_scoring=use_severity_weighted_scoring,
                include_gold=include_gold,
            )
            progress_metrics["progress"] = {
                "completed_items": index,
                "total_items": total_items,
                "fraction": index / total_items if total_items else 1.0,
            }
            write_json(output_dir / "metrics_progress.json", progress_metrics)
            progress_callback(index, total_items, progress_metrics)

    metrics = _compute_metrics(
        items,
        results,
        dataset_metadata=dataset_metadata,
        use_severity_weighted_scoring=use_severity_weighted_scoring,
        include_gold=include_gold,
    )
    manual_review_count = sum(
        1 for result in results if _needs_manual_review_export(result)
    )
    metrics["artifacts"]["manual_review_rows"] = manual_review_count
    metrics["artifacts"]["manual_review_file"] = (
        "manual_review.jsonl" if write_predictions else None
    )

    if write_predictions and not write_predictions_incrementally:
        write_jsonl(
            output_dir / "predictions.jsonl",
            [
                _prediction_record(
                    result,
                    opaque_id=_opaque_eval_id(index),
                    include_gold=include_gold,
                )
                for index, result in enumerate(results, start=1)
            ],
        )
        write_jsonl(
            output_dir / "manual_review.jsonl",
            [
                _manual_review_record(result, opaque_id=_opaque_eval_id(index))
                for index, result in enumerate(results, start=1)
                if _needs_manual_review_export(result)
            ],
        )
    write_json(output_dir / "metrics.json", metrics)
    if write_report:
        write_markdown_report(output_dir / "report.md", metrics)
    return metrics
