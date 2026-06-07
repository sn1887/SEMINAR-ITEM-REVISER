from __future__ import annotations

import subprocess
import sys


def main() -> None:
    # Simple sequential launcher. For serious sweeps, use Hydra multirun directly.
    models = ["mock"]
    for model in models:
        print(f"Running benchmark for model={model}")
        subprocess.run([sys.executable, "scripts/evaluate.py", f"model={model}"], check=True)


if __name__ == "__main__":
    main()
