#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import resource


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVALUATE_SCRIPT = REPO_ROOT / "scripts" / "evaluate.py"
DEFAULT_MODEL_ROOT = "/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models"
DEFAULT_EXPERIMENT_NAME = "item_reviser_eval"


def _safe_component(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in raw)


@dataclass
class BenchmarkRun:
    phase: str
    stage: str
    model_label: str
    model_path: str | None
    max_items: int | str | None
    run_name: str
    experiment_name: str
    seed: int


def _build_runs(phase: str, model_root: str) -> list[BenchmarkRun]:
    smoke = [
        BenchmarkRun(
            "smoke",
            "smoke__mock",
            "mock",
            None,
            5,
            "smoke__mock_5",
            "item_reviser_benchmark_smoke",
            420,
        ),
        BenchmarkRun(
            "smoke",
            "smoke__hf",
            "Qwen2.5-1.5B-Instruct",
            f"{model_root}/Qwen2.5-1.5B-Instruct",
            5,
            "smoke__hf_qwen2_5_1_5b",
            "item_reviser_benchmark_smoke",
            421,
        ),
    ]
    shortlist_5 = [
        BenchmarkRun(
            "shortlist-5",
            "shortlist5",
            "Qwen2.5-1.5B-Instruct",
            f"{model_root}/Qwen2.5-1.5B-Instruct",
            5,
            "shortlist5__hf_qwen2_5-1_5b",
            "item_reviser_benchmark_shortlist_5",
            520,
        ),
        BenchmarkRun(
            "shortlist-5",
            "shortlist5",
            "Qwen3-1.7B",
            f"{model_root}/Qwen3-1.7B",
            5,
            "shortlist5__hf_qwen3_1_7b",
            "item_reviser_benchmark_shortlist_5",
            521,
        ),
        BenchmarkRun(
            "shortlist-5",
            "shortlist5",
            "Qwen2.5-7B-Instruct",
            f"{model_root}/Qwen2.5-7B-Instruct",
            5,
            "shortlist5__hf_qwen2_5_7b",
            "item_reviser_benchmark_shortlist_5",
            522,
        ),
        BenchmarkRun(
            "shortlist-5",
            "shortlist5",
            "Mistral-7B-Instruct-v0.3",
            f"{model_root}/Mistral-7B-Instruct-v0.3",
            5,
            "shortlist5__hf_mistral_7b",
            "item_reviser_benchmark_shortlist_5",
            523,
        ),
        BenchmarkRun(
            "shortlist-5",
            "shortlist5",
            "Phi-3-mini-128k-instruct",
            f"{model_root}/Phi-3-mini-128k-instruct",
            5,
            "shortlist5__hf_phi3_mini",
            "item_reviser_benchmark_shortlist_5",
            524,
        ),
    ]
    shortlist_20 = [
        BenchmarkRun(
            "shortlist-20",
            "shortlist20",
            "Qwen2.5-7B-Instruct",
            f"{model_root}/Qwen2.5-7B-Instruct",
            20,
            "shortlist20__hf_qwen2_5_7b",
            "item_reviser_benchmark_shortlist_20",
            620,
        ),
        BenchmarkRun(
            "shortlist-20",
            "shortlist20",
            "Qwen2.5-14B-Instruct",
            f"{model_root}/Qwen2.5-14B-Instruct",
            20,
            "shortlist20__hf_qwen2_5_14b",
            "item_reviser_benchmark_shortlist_20",
            621,
        ),
        BenchmarkRun(
            "shortlist-20",
            "shortlist20",
            "gemma-2-9b-it",
            f"{model_root}/gemma-2-9b-it",
            20,
            "shortlist20__hf_gemma-2-9b-it",
            "item_reviser_benchmark_shortlist_20",
            622,
        ),
        BenchmarkRun(
            "shortlist-20",
            "shortlist20",
            "gpt-oss-20b",
            f"{model_root}/gpt-oss-20b",
            20,
            "shortlist20__hf_gpt_oss_20b",
            "item_reviser_benchmark_shortlist_20",
            623,
        ),
        BenchmarkRun(
            "shortlist-20",
            "shortlist20",
            "Qwen3.5-9B",
            f"{model_root}/Qwen3.5-9B",
            20,
            "shortlist20__hf_qwen3_5_9b",
            "item_reviser_benchmark_shortlist_20",
            624,
        ),
    ]
    full_200 = [
        BenchmarkRun(
            "full-200",
            "full200",
            "Qwen2.5-7B-Instruct",
            f"{model_root}/Qwen2.5-7B-Instruct",
            "all",
            "full200__hf_qwen2_5_7b",
            "item_reviser_benchmark_full_200",
            720,
        ),
        BenchmarkRun(
            "full-200",
            "full200",
            "Qwen2.5-14B-Instruct",
            f"{model_root}/Qwen2.5-14B-Instruct",
            "all",
            "full200__hf_qwen2_5_14b",
            "item_reviser_benchmark_full_200",
            721,
        ),
        BenchmarkRun(
            "full-200",
            "full200",
            "gpt-oss-20b",
            f"{model_root}/gpt-oss-20b",
            "all",
            "full200__hf_gpt_oss_20b",
            "item_reviser_benchmark_full_200",
            722,
        ),
    ]
    vision_20 = [
        BenchmarkRun(
            "vision-20",
            "vision20",
            "Qwen2.5-VL-7B-Instruct",
            f"{model_root}/Qwen2.5-VL-7B-Instruct",
            20,
            "vision20__hf_qwen2_5-vl_7b",
            "item_reviser_benchmark_vision_20",
            820,
        ),
        BenchmarkRun(
            "vision-20",
            "vision20",
            "MiniCPM-o-2_6",
            f"{model_root}/MiniCPM-o-2_6",
            20,
            "vision20__hf_minicpm_o_2_6",
            "item_reviser_benchmark_vision_20",
            821,
        ),
    ]

    if phase == "smoke":
        return [*smoke]
    if phase == "shortlist-5":
        return [*shortlist_5]
    if phase == "shortlist-20":
        return [*shortlist_20]
    if phase == "full-200":
        return [*full_200]
    if phase == "vision-20":
        return [*vision_20]
    if phase == "all":
        return [*smoke, *shortlist_5, *shortlist_20, *full_200, *vision_20]
    raise ValueError(f"Unknown phase: {phase}")


def _build_command(
    run: BenchmarkRun,
    tracking_uri: str,
    max_items_override: int | str | None = None,
    warmup: bool = False,
) -> list[str]:
    tracking_run_name = f"{run.run_name}__warmup" if warmup else run.run_name
    args = [
        "python",
        str(DEFAULT_EVALUATE_SCRIPT),
        f"experiment={DEFAULT_EXPERIMENT_NAME}",
        f"tracking.experiment_name={run.experiment_name}",
        f"seed={run.seed}",
        f"tracking.run_name={tracking_run_name}",
        "tracking.enabled=true",
        f"tracking.tracking_uri={tracking_uri}",
    ]

    max_items = max_items_override if max_items_override is not None else run.max_items
    if max_items != "all" and max_items is not None:
        args.append(f"experiment.max_items={max_items}")

    if run.model_label == "mock":
        args.append("model=mock")
    else:
        args.extend(
            [
                "model=hf_local",
                f"model.model_path={run.model_path}",
            ]
        )
    if warmup:
        args.extend(
            [
                "experiment.write_predictions=false",
                "experiment.write_report=false",
            ]
        )
    return args


def _mark_status(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            run_name = str(payload.get("run_name", ""))
            if payload.get("is_warmup"):
                continue
            if payload.get("attempt", 0) == 0:
                continue
            if payload.get("status") == "success":
                completed.add(run_name)
    return completed


def _run_once(
    run: BenchmarkRun,
    log_file: Path,
    args: list[str],
    timeout_seconds: int,
    status_file: Path,
    attempt: int,
    phase_name: str,
    is_warmup: bool = False,
) -> tuple[bool, dict[str, Any]]:
    child_env = os.environ.copy()
    existing_pythonpath = child_env.get("PYTHONPATH", "")
    runtime_paths = [str(REPO_ROOT / "src")]
    if existing_pythonpath:
        runtime_paths.append(existing_pythonpath)
    child_env["PYTHONPATH"] = os.pathsep.join(runtime_paths)

    run_name = run.run_name
    attempt_run_id = f"{run_name}__{'warmup' if is_warmup else f'attempt_{attempt}'}"
    start = time.perf_counter()
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    try:
        with log_file.open("a", encoding="utf-8") as log:
            log.write(f"\\n[{datetime.now().isoformat()}] Starting run {attempt_run_id}\\n")
            log.write(" ".join(args) + "\\n")
            completed = subprocess.run(
                args,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=timeout_seconds,
                env=child_env,
            )
            return_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        return_code = 124
        with log_file.open("a", encoding="utf-8") as log:
            log.write(f"\\nTimeout after {timeout_seconds} seconds\\n{exc}\\n")
    except Exception as exc:
        return_code = 255
        with log_file.open("a", encoding="utf-8") as log:
            log.write(f"\\nExecution error: {exc}\\n")

    elapsed_ms = (time.perf_counter() - start) * 1000
    child_after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_kb = max(0, child_after - child_before)
    status = {
        "run_name": run_name,
        "phase": phase_name,
        "stage": run.stage,
        "model_label": run.model_label,
        "model_path": run.model_path,
        "max_items": run.max_items,
        "attempt": attempt,
        "is_warmup": is_warmup,
        "attempt_run_id": attempt_run_id,
        "return_code": return_code,
        "duration_ms": elapsed_ms,
        "ru_maxrss_kb_delta": peak_kb,
        "status": "success" if return_code == 0 else "failure",
        "timestamp": datetime.now().isoformat(),
        "seed": run.seed,
    }
    _mark_status(status_file, status)
    return status["status"] == "success", status


def run_phase(
    phase: str,
    model_root: str,
    attempts: int,
    timeout: int,
    resume: bool,
    status_file: Path,
    run_root: Path,
    tracking_uri: str,
) -> list[dict[str, Any]]:
    runs = _build_runs(phase, model_root)
    completed = _load_completed(status_file) if resume else set()
    statuses: list[dict[str, Any]] = []
    for run in runs:
        run_log = run_root / f"{_safe_component(run.run_name)}.log"
        if run.run_name in completed:
            skipped = {
                "run_name": run.run_name,
                "phase": run.phase,
                "stage": run.stage,
                "model_label": run.model_label,
                "max_items": run.max_items,
                "status": "skipped",
                "reason": "already_successful",
                "timestamp": datetime.now().isoformat(),
            }
            statuses.append(skipped)
            _mark_status(status_file, skipped)
            continue

        # Short warmup for environment/cache priming.
        warmup_cmd = _build_command(
            run,
            tracking_uri=tracking_uri,
            max_items_override=1,
            warmup=True,
        )
        _run_once(
            run=run,
            log_file=run_log,
            args=warmup_cmd,
            timeout_seconds=min(timeout, 600),
            status_file=status_file,
            attempt=0,
            phase_name=run.phase,
            is_warmup=True,
        )

        success = False
        last_status: dict[str, Any] = {
            "run_name": run.run_name,
            "phase": run.phase,
            "status": "failed",
            "reason": "not_run",
            "timestamp": datetime.now().isoformat(),
        }
        for attempt in range(1, attempts + 1):
            cmd = _build_command(
                run,
                tracking_uri=tracking_uri,
                max_items_override=None,
                warmup=False,
            )
            success, last_status = _run_once(
                run=run,
                log_file=run_log,
                args=cmd,
                timeout_seconds=timeout,
                status_file=status_file,
                attempt=attempt,
                phase_name=run.phase,
            )
            if success:
                last_status["status"] = "success"
                break
            if attempt < attempts:
                time.sleep(min(2.0 * attempt, 10.0))

        if not success:
            last_status = {**last_status, "status": "failed"}
        statuses.append(last_status)
    return statuses


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        default="all",
        choices=["smoke", "shortlist-5", "shortlist-20", "full-200", "vision-20", "all"],
    )
    parser.add_argument("--model-root", default=DEFAULT_MODEL_ROOT)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.add_argument("--run-root", default="")
    parser.set_defaults(resume=True)
    args = parser.parse_args()

    run_root = Path(args.run_root) if args.run_root else Path("logs/benchmarks") / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root.mkdir(parents=True, exist_ok=True)
    status_file = run_root / "phase_status.jsonl"

    tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI",
        f"file://{REPO_ROOT / 'mlruns'}",
    )

    statuses = run_phase(
        phase=args.phase,
        model_root=args.model_root,
        attempts=args.attempts,
        timeout=args.timeout,
        resume=args.resume,
        status_file=status_file,
        run_root=run_root,
        tracking_uri=tracking_uri,
    )

    summary = {
        "phase": args.phase,
        "run_root": str(run_root),
        "runs_total": len(statuses),
        "runs_executed": len([s for s in statuses if s.get("status") != "skipped"]),
        "runs_skipped": len([s for s in statuses if s.get("status") == "skipped"]),
        "failures": len([s for s in statuses if s.get("status") == "failed"]),
        "status_file": str(status_file),
    }
    _mark_status(status_file, {"summary": summary})
    print(json.dumps(summary, sort_keys=True))
    if summary["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
