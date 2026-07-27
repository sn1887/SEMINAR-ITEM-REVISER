"""Populate and verify the semantic metric cache before expensive final runs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from item_reviser.evaluation.metrics import MetricConfig, SemanticRevisionMetrics  # noqa: E402
from item_reviser.schemas import PipelineResult, RevisedItem, SurveyItem  # noqa: E402


def _smoke_item() -> SurveyItem:
    return SurveyItem(
        id="metric-cache-smoke",
        question="Don't you agree that the service was excellent?",
        response_options=["Strongly disagree", "Disagree", "Agree", "Strongly agree"],
        known_errors=["leading_question", "agree_disagree_scale"],
        expected_revision={
            "question": "How satisfied or dissatisfied were you with the service?",
            "response_options": [
                "Very dissatisfied",
                "Somewhat dissatisfied",
                "Neither satisfied nor dissatisfied",
                "Somewhat satisfied",
                "Very satisfied",
            ],
            "revision_notes": ["Remove leading wording and use a direct satisfaction scale."],
        },
    )


def _smoke_result(item: SurveyItem) -> PipelineResult:
    expected = item.expected_revision
    assert isinstance(expected, dict)
    return PipelineResult(
        item_id=item.id,
        original_item=item,
        detected_errors=[],
        revised_item=RevisedItem(
            question=str(expected["question"]),
            response_options=[str(option) for option in expected["response_options"]],
            revision_notes=["Metric cache smoke revision."],
            changed=True,
        ),
    )


def _phase_summary(config: MetricConfig) -> dict[str, Any]:
    suite = SemanticRevisionMetrics(config)
    metadata = suite.preflight()
    item = _smoke_item()
    revision = suite.score([item], [_smoke_result(item)])
    for metric_name in ("question_bertscore_f1", "sari"):
        value = revision[metric_name]["value"]
        if value is None:
            raise RuntimeError(f"{metric_name} returned no value during metric-cache preflight.")
    return {
        "metric_config": metadata["metric_config"],
        "bertscore_hash": metadata["bertscore_hash"],
        "package_versions": metadata["package_versions"],
        "smoke_metrics": {
            "question_bertscore_f1": revision["question_bertscore_f1"]["value"],
            "sari": revision["sari"]["value"],
        },
    }


def run_metric_cache_preflight(
    config: MetricConfig,
    *,
    connected: bool = True,
    offline: bool = True,
) -> dict[str, Any]:
    if not connected and not offline:
        raise ValueError("At least one metric-cache preflight phase must be enabled.")
    result: dict[str, Any] = {}
    if connected:
        result["connected"] = _phase_summary(replace(config, offline=False))
    if offline:
        result["offline"] = _phase_summary(replace(config, offline=True))
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-path", default=".metric-cache")
    parser.add_argument("--model-type", default="distilroberta-base")
    parser.add_argument("--num-layers", type=int, default=5)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--language", default="en")
    parser.add_argument("--rescale-with-baseline", choices=("true", "false"), default="false")
    parser.add_argument("--connected-only", action="store_true")
    parser.add_argument("--offline-only", action="store_true")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.connected_only and args.offline_only:
        parser.error("--connected-only and --offline-only are mutually exclusive")
    config = MetricConfig(
        bertscore_model_type=args.model_type,
        bertscore_num_layers=args.num_layers,
        device=args.device,
        batch_size=args.batch_size,
        rescale_with_baseline=args.rescale_with_baseline == "true",
        language=args.language,
        cache_path=args.cache_path,
        offline=False,
    )
    summary = run_metric_cache_preflight(
        config,
        connected=not args.offline_only,
        offline=not args.connected_only,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
