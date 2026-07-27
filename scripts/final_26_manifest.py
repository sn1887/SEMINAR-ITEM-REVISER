"""Read and validate the frozen final 26-run seminar experiment matrix."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "experiments" / "final_26_run_manifest.jsonl"
BLOCK_COUNTS = {"A": 12, "B": 4, "C": 4, "D": 4, "E": 2}
REQUIRED_FIELDS = {
    "run_id",
    "block",
    "model_slug",
    "model_path",
    "model_label",
    "prompt_pack",
    "prompt_config",
    "pipeline",
    "orchestration_enabled",
    "evaluation_mode",
    "thinking",
    "data_config",
    "dataset_version",
    "decoding",
}
EXPECTED_PROMPTS = {
    ("P0", "baseline"): "baseline_codebook",
    ("P0", "orchestrated"): "orchestration_codebook",
    ("P1", "baseline"): "baseline_p1",
    ("P1", "orchestrated"): "orchestration_p1",
    ("P2", "baseline"): "baseline_p2",
    ("P2", "orchestrated"): "orchestration_p2",
}
REFERENCE_DECODING = {
    "method": "greedy",
    "max_new_tokens": 2048,
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": None,
    "num_beams": 1,
    "repetition_penalty": None,
}
MODEL_PATHS = {
    "mistral7b_v03": "/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/Mistral-7B-Instruct-v0.3",
    "gemma2_9b": "/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/gemma-2-9b-it",
    "qwen35_9b": "/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/Qwen3.5-9B",
}


def _expected_conditions() -> set[tuple[str, str, str, str, str, bool]]:
    modes = ("end_to_end", "oracle_revision")
    pipelines = ("baseline", "orchestrated")
    conditions = {
        ("A", model, "P0", pipeline, mode, False)
        for model in MODEL_PATHS
        for pipeline in pipelines
        for mode in modes
    }
    for block, pack, thinking in (("B", "P1", False), ("C", "P2", False), ("D", "P2", True)):
        conditions.update(
            (block, "qwen35_9b", pack, pipeline, mode, thinking)
            for pipeline in pipelines
            for mode in modes
        )
    conditions.update(
        ("E", "gemma2_9b", "P2", pipeline, "end_to_end", False)
        for pipeline in pipelines
    )
    return conditions


def load_manifest(path: Path = DEFAULT_MANIFEST) -> list[dict[str, Any]]:
    """Load a JSONL manifest while retaining line-numbered parse failures."""
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: expected an object")
        rows.append(row)
    return rows


def selected_rows(rows: Iterable[dict[str, Any]], blocks: set[str] | None) -> list[dict[str, Any]]:
    return [row for row in rows if blocks is None or row["block"] in blocks]


def _check_config_files(rows: Iterable[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    data_configs = {str(row["data_config"]) for row in rows}
    prompt_configs = {str(row["prompt_config"]) for row in rows}
    for config_name in sorted(data_configs):
        if not (REPO_ROOT / "configs" / "data" / f"{config_name}.yaml").is_file():
            errors.append(f"missing Hydra data config: {config_name}")
    for config_name in sorted(prompt_configs):
        if not (REPO_ROOT / "configs" / "prompt" / f"{config_name}.yaml").is_file():
            errors.append(f"missing Hydra prompt config: {config_name}")
    return errors


def validate_manifest(
    rows: list[dict[str, Any]], *, check_files: bool = True
) -> list[str]:
    """Return every static manifest violation instead of failing at the first."""
    errors: list[str] = []
    if len(rows) != 26:
        errors.append(f"expected exactly 26 rows, found {len(rows)}")
    counts = Counter(str(row.get("block")) for row in rows)
    if dict(sorted(counts.items())) != BLOCK_COUNTS:
        errors.append(f"block counts must be {BLOCK_COUNTS}, found {dict(sorted(counts.items()))}")

    run_ids = [str(row.get("run_id")) for row in rows]
    duplicates = sorted(run_id for run_id, count in Counter(run_ids).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate run_id values: {duplicates}")

    actual_conditions = {
        (
            row.get("block"),
            row.get("model_slug"),
            row.get("prompt_pack"),
            row.get("pipeline"),
            row.get("evaluation_mode"),
            row.get("thinking"),
        )
        for row in rows
    }
    expected_conditions = _expected_conditions()
    if actual_conditions != expected_conditions or len(actual_conditions) != len(rows):
        errors.append("rows do not exactly match the preregistered block/model/pipeline/mode matrix")

    for index, row in enumerate(rows, start=1):
        label = f"row {index} ({row.get('run_id', '<missing>')})"
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            errors.append(f"{label}: missing fields {sorted(missing)}")
            continue
        block = row["block"]
        pipeline = row["pipeline"]
        prompt_pack = row["prompt_pack"]
        if row["model_path"] != MODEL_PATHS.get(row["model_slug"]):
            errors.append(f"{label}: model path does not match the registered model slug")
        if block not in BLOCK_COUNTS:
            errors.append(f"{label}: unsupported block {block!r}")
        if pipeline not in {"baseline", "orchestrated"}:
            errors.append(f"{label}: unsupported pipeline {pipeline!r}")
        elif bool(row["orchestration_enabled"]) != (pipeline == "orchestrated"):
            errors.append(f"{label}: orchestration_enabled does not match pipeline")
        if row["evaluation_mode"] not in {"end_to_end", "oracle_revision"}:
            errors.append(f"{label}: detection_only is not part of the final matrix")
        if row["data_config"] != "final_gold_200_v4" or row["dataset_version"] != "v4":
            errors.append(f"{label}: every final run must use final_gold_200_v4 / v4")
        expected_prompt = EXPECTED_PROMPTS.get((prompt_pack, pipeline))
        if expected_prompt is None or row["prompt_config"] != expected_prompt:
            errors.append(f"{label}: prompt pack/config does not match the matrix")
        if row["decoding"] != REFERENCE_DECODING:
            errors.append(f"{label}: decoding differs from the frozen ablation settings")
        if bool(row["thinking"]) != (block == "D"):
            errors.append(f"{label}: only block D may enable thinking")
        if block in {"B", "C", "D"} and row["model_slug"] != "qwen35_9b":
            errors.append(f"{label}: blocks B-D must use Qwen3.5-9B")
        if block == "E" and (
            row["model_slug"] != "gemma2_9b" or row["evaluation_mode"] != "end_to_end"
        ):
            errors.append(f"{label}: block E is Gemma P2 end-to-end only")
        if block == "A" and prompt_pack != "P0":
            errors.append(f"{label}: block A must be P0")
        if block == "B" and prompt_pack != "P1":
            errors.append(f"{label}: block B must be P1")
        if block in {"C", "D", "E"} and prompt_pack != "P2":
            errors.append(f"{label}: blocks C-E must be P2")

    if check_files:
        errors.extend(_check_config_files(rows))
        data_path = REPO_ROOT / "data" / "final_gold_200_v4" / "final_gold_200_unique_v4.jsonl"
        if not data_path.is_file():
            errors.append(f"canonical v4 dataset is missing: {data_path}")
    return errors


def hydra_overrides(row: dict[str, Any], *, git_commit: str) -> list[str]:
    """Build the complete, explicit override set used by one scheduled job."""
    decoding = row["decoding"]

    def value(item: object) -> str:
        if item is None:
            return "null"
        if isinstance(item, bool):
            return str(item).lower()
        return str(item)

    return [
        "experiment=final_26_run_matrix",
        f"data={row['data_config']}",
        "model=hf_local",
        f"model.model_path={row['model_path']}",
        f"model.chat_template.enable_thinking={value(row['thinking'])}",
        f"model.decoding.method={decoding['method']}",
        f"model.decoding.max_new_tokens={decoding['max_new_tokens']}",
        f"model.decoding.temperature={decoding['temperature']}",
        f"model.decoding.top_p={decoding['top_p']}",
        f"model.decoding.top_k={value(decoding['top_k'])}",
        f"model.decoding.num_beams={decoding['num_beams']}",
        f"model.decoding.repetition_penalty={value(decoding['repetition_penalty'])}",
        f"prompt={row['prompt_config']}",
        f"orchestration.enabled={value(row['orchestration_enabled'])}",
        f"evaluator.mode={row['evaluation_mode']}",
        "evaluator.continue_on_item_error=true",
        "evaluator.write_predictions_incrementally=true",
        "evaluator.include_gold=false",
        "evaluator.metric_config.cache_path=${oc.env:METRIC_CACHE_PATH,.metric-cache}",
        "evaluator.metric_config.offline=${oc.env:METRIC_OFFLINE,false}",
        "tracking.enabled=true",
        "tracking.log_progress_every_items=${oc.env:PROGRESS_INTERVAL,10}",
        "tracking.experiment_name=${oc.env:MLFLOW_EXPERIMENT_NAME,seminar-item-reviser-final-26}",
        "tracking.run_name=${oc.env:RUN_NAME}",
        f"experiment.run_id={row['run_id']}",
        f"experiment.matrix_block={row['block']}",
        f"experiment.prompt_pack={row['prompt_pack']}",
        f"experiment.pipeline={row['pipeline']}",
        f"experiment.thinking={value(row['thinking'])}",
        f"experiment.git_commit={git_commit}",
        "hydra.run.dir=${oc.env:HYDRA_OUTPUT_DIR}",
    ]


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _parse_blocks(value: str | None) -> set[str] | None:
    if not value:
        return None
    blocks = {block.strip().upper() for block in value.split(",") if block.strip()}
    unknown = blocks - set(BLOCK_COUNTS)
    if unknown:
        raise ValueError(f"unknown blocks: {', '.join(sorted(unknown))}")
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "list", "overrides"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--blocks", help="Comma-separated subset of A,B,C,D,E.")
    parser.add_argument("--run-id", help="Required for the overrides command.")
    parser.add_argument("--check-hydra", action="store_true", help="Compose each selected row via Hydra.")
    args = parser.parse_args()

    try:
        rows = load_manifest(args.manifest)
        errors = validate_manifest(rows)
        blocks = _parse_blocks(args.blocks)
    except ValueError as exc:
        print(f"Manifest validation error: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("Manifest validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 2

    selected = selected_rows(rows, blocks)
    if args.check_hydra:
        for row in selected:
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "evaluate.py"),
                "--cfg",
                "job",
                "--resolve",
                *hydra_overrides(row, git_commit="preflight"),
            ]
            environment = {
                **os.environ,
                "RUN_NAME": "preflight",
                "HYDRA_OUTPUT_DIR": "outputs/preflight",
                "PROGRESS_INTERVAL": "10",
                "METRIC_CACHE_PATH": ".metric-cache",
                "MLFLOW_EXPERIMENT_NAME": "seminar-item-reviser-final-26",
            }
            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
            )
            if result.returncode:
                print(f"Hydra composition failed for {row['run_id']}:\n{result.stderr}", file=sys.stderr)
                return result.returncode

    if args.command == "validate":
        print(f"Validated {len(rows)} unique final-matrix runs: " + ", ".join(
            f"{block}={BLOCK_COUNTS[block]}" for block in BLOCK_COUNTS
        ))
        if blocks is not None:
            print(f"Selected {len(selected)} run(s) from blocks {','.join(sorted(blocks))}.")
        return 0
    if args.command == "list":
        for row in selected:
            print(json.dumps(row, sort_keys=True))
        return 0
    if not args.run_id:
        parser.error("--run-id is required for overrides")
    matching = [row for row in rows if row["run_id"] == args.run_id]
    if len(matching) != 1:
        print(f"Unknown run_id: {args.run_id}", file=sys.stderr)
        return 2
    print(json.dumps(hydra_overrides(matching[0], git_commit=_git_commit())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
