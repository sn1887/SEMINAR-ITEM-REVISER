"""Validate and launch the router-control runs (shared detection prompts).

The control manifest re-runs selected rows of the frozen final matrix with one
change: orchestrated rows use the orchestration_shared_* prompt configs, whose
router carries the baseline checker's detection text. A baseline "repro" row
re-runs an unchanged August condition to check that the environment still
reproduces the archived results.

Every control row must equal its August row (``control_of``) in all fields
except run_id, block, prompt_config and the control_* bookkeeping fields, so
model, decoding, data and evaluation mode cannot drift.

Examples:
    python scripts/run_router_control.py validate
    python scripts/run_router_control.py list
    python scripts/run_router_control.py run --run-id r_p0_qwen35_9b_orchestrated_end_to_end_shared
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from final_26_manifest import (
    EXPECTED_PROMPTS,
    REPO_ROOT,
    hydra_overrides,
    load_manifest,
    validate_manifest,
)

CONTROL_MANIFEST = REPO_ROOT / "experiments" / "router_control_manifest.jsonl"
CONTROL_BLOCK = "R"
CONTROL_KINDS = {"shared", "repro"}
MUTABLE_FIELDS = {"run_id", "block", "prompt_config", "control_of", "control_kind"}
MLFLOW_EXPERIMENT = "seminar-item-reviser-router-control"
RUN_ID_RE = re.compile(r"[a-z0-9_]+")


def load_control_manifest(path: Path = CONTROL_MANIFEST) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name} line {number}: invalid JSON ({exc})") from exc
    return rows


def expected_prompt(row: dict[str, Any]) -> str:
    original = EXPECTED_PROMPTS[(row["prompt_pack"], row["pipeline"])]
    if row["control_kind"] == "repro":
        return original
    if row["pipeline"] != "orchestrated":
        raise ValueError("shared-router controls apply to orchestrated rows only")
    return original.replace("orchestration_", "orchestration_shared_", 1)


def validate_control_manifest(
    rows: list[dict[str, Any]], final_rows: list[dict[str, Any]]
) -> list[str]:
    errors = [f"final matrix: {error}" for error in validate_manifest(final_rows)]
    final_by_id = {row["run_id"]: row for row in final_rows}
    seen: set[str] = set()
    sources_seen: set[str] = set()
    for row in rows:
        run_id = row.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
            errors.append(f"{run_id!r}: run_id must match [a-z0-9_]+")
            continue
        if run_id in seen:
            errors.append(f"{run_id}: duplicate run_id")
        seen.add(run_id)
        if run_id in final_by_id:
            errors.append(f"{run_id}: collides with a final-matrix run_id")
        if row.get("block") != CONTROL_BLOCK:
            errors.append(f"{run_id}: block must be {CONTROL_BLOCK}")
        if row.get("control_kind") not in CONTROL_KINDS:
            errors.append(f"{run_id}: control_kind must be one of {sorted(CONTROL_KINDS)}")
            continue
        source = final_by_id.get(row.get("control_of"))
        if source is None:
            errors.append(f"{run_id}: control_of does not name a final-matrix run")
            continue
        if source["run_id"] in sources_seen:
            errors.append(f"{run_id}: {source['run_id']} is controlled more than once")
        sources_seen.add(source["run_id"])
        if source["thinking"]:
            errors.append(f"{run_id}: thinking runs are not part of the control")
        if set(row) - MUTABLE_FIELDS != set(source) - {"run_id", "block", "prompt_config"}:
            errors.append(f"{run_id}: field set differs from {source['run_id']}")
        for key, value in source.items():
            if key in MUTABLE_FIELDS:
                continue
            if row.get(key) != value:
                errors.append(f"{run_id}: {key} differs from {source['run_id']}")
        try:
            wanted = expected_prompt(row)
        except (KeyError, ValueError) as exc:
            errors.append(f"{run_id}: {exc}")
            continue
        if row.get("prompt_config") != wanted:
            errors.append(f"{run_id}: prompt_config must be {wanted}")
        if not (REPO_ROOT / "configs" / "prompt" / f"{wanted}.yaml").is_file():
            errors.append(f"{run_id}: missing Hydra prompt config {wanted}")
    return errors


def control_overrides(row: dict[str, Any], *, git_commit: str) -> list[str]:
    overrides = hydra_overrides(row, git_commit=git_commit)
    overrides.append(
        "experiment.matrix_manifest="
        + str(CONTROL_MANIFEST.relative_to(REPO_ROOT))
    )
    return overrides


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def check_hydra(rows: list[dict[str, Any]]) -> list[str]:
    """Compose each row with Hydra, as the August preflight did, without running it."""
    failures = []
    environment = {
        **os.environ,
        "RUN_NAME": "preflight",
        "HYDRA_OUTPUT_DIR": "outputs/preflight",
        "PROGRESS_INTERVAL": "10",
        "METRIC_CACHE_PATH": os.environ.get("METRIC_CACHE_PATH", ".metric-cache"),
        "MLFLOW_EXPERIMENT_NAME": MLFLOW_EXPERIMENT,
    }
    for row in rows:
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "evaluate.py"),
            "--cfg",
            "job",
            "--resolve",
            *control_overrides(row, git_commit="preflight"),
        ]
        result = subprocess.run(command, cwd=REPO_ROOT, env=environment, text=True, capture_output=True)
        if result.returncode:
            failures.append(f"Hydra composition failed for {row['run_id']}:\n{result.stderr}")
    return failures


def _checked_rows(parser: argparse.ArgumentParser) -> list[dict[str, Any]]:
    try:
        rows = load_control_manifest()
    except ValueError as exc:
        parser.error(str(exc))
    errors = validate_control_manifest(rows, load_manifest())
    if errors:
        parser.error("invalid router-control manifest: " + "; ".join(errors))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--check-hydra", action="store_true", help="compose every row via Hydra")
    sub.add_parser("list")
    run = sub.add_parser("run")
    run.add_argument("--run-id", required=True)
    args = parser.parse_args()

    rows = _checked_rows(parser)
    if args.command == "validate":
        missing = [row["run_id"] for row in rows if not Path(row["model_path"]).is_dir()]
        if missing:
            print("Model paths unavailable for: " + ", ".join(missing), file=sys.stderr)
            return 1
        if args.check_hydra:
            failures = check_hydra(rows)
            if failures:
                print("\n".join(failures), file=sys.stderr)
                return 1
        print(f"Router-control manifest valid: {len(rows)} runs" + (" (Hydra composed)" if args.check_hydra else ""))
        return 0
    if args.command == "list":
        for row in rows:
            print(json.dumps(row, separators=(",", ":")))
        return 0

    matching = [row for row in rows if row["run_id"] == args.run_id]
    if len(matching) != 1:
        parser.error(f"unknown run_id: {args.run_id}")
    row = matching[0]
    if not Path(row["model_path"]).is_dir():
        parser.error(f"model path is unavailable: {row['model_path']}")
    run_group = os.environ.get("RUN_GROUP")
    if not run_group:
        parser.error("RUN_GROUP must be set by the submitter")
    os.environ.setdefault("RUN_NAME", row["run_id"])
    output_dir = os.environ.setdefault("HYDRA_OUTPUT_DIR", f"outputs/{run_group}/{row['run_id']}")
    os.environ.setdefault("MLFLOW_TRACKING_URI", f"file://{REPO_ROOT / 'mlruns' / run_group}")
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    os.environ.setdefault("MLFLOW_EXPERIMENT_NAME", MLFLOW_EXPERIMENT)
    os.environ.setdefault("PROGRESS_INTERVAL", "10")
    os.environ.setdefault("METRIC_CACHE_PATH", ".metric-cache")

    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "evaluate.py"),
        *control_overrides(row, git_commit=_git_commit()),
    ]
    print("Router-control run:", row["run_id"], "(control of", row["control_of"] + ")")
    print("Hydra output:", output_dir)
    print("Command:", json.dumps(command))
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
