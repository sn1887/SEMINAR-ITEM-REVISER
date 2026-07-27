"""Launch one frozen final-matrix row from Slurm without duplicating overrides."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from final_26_manifest import REPO_ROOT, hydra_overrides, load_manifest, validate_manifest


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    rows = load_manifest()
    errors = validate_manifest(rows)
    if errors:
        parser.error("invalid final matrix: " + "; ".join(errors))
    matching = [row for row in rows if row["run_id"] == args.run_id]
    if len(matching) != 1:
        parser.error(f"unknown run_id: {args.run_id}")
    row = matching[0]
    model_path = Path(row["model_path"])
    if not model_path.is_dir():
        parser.error(f"model path is unavailable: {model_path}")

    run_group = os.environ.get("RUN_GROUP")
    if not run_group:
        parser.error("RUN_GROUP must be set by the submitter")
    run_name = os.environ.setdefault("RUN_NAME", row["run_id"])
    output_dir = os.environ.setdefault("HYDRA_OUTPUT_DIR", f"outputs/{run_group}/{run_name}")
    os.environ.setdefault(
        "MLFLOW_TRACKING_URI", f"file://{REPO_ROOT / 'mlruns' / run_group}"
    )
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    os.environ.setdefault("MLFLOW_EXPERIMENT_NAME", "seminar-item-reviser-final-26")
    os.environ.setdefault("PROGRESS_INTERVAL", "10")
    os.environ.setdefault("METRIC_CACHE_PATH", ".metric-cache")

    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "evaluate.py"),
        *hydra_overrides(row, git_commit=_git_commit()),
    ]
    print("Final matrix run:", row["run_id"])
    print("Hydra output:", output_dir)
    print("MLflow URI:", os.environ["MLFLOW_TRACKING_URI"])
    print("Command:", json.dumps(command))
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
