from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object rows in {path}")
        rows.append(payload)
    return rows


def _string_list(value: Any) -> str:
    if not value:
        return "(none)"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def _infer_title(path: Path, rows: list[dict[str, Any]]) -> str:
    if path.stem:
        return path.stem
    return f"dataset_{len(rows)}"


def _build_summary(rows: list[dict[str, Any]]) -> list[str]:
    topic_counts = Counter(str(row.get("topic", "unknown")) for row in rows)
    label_counts = Counter(
        label
        for row in rows
        for label in (row.get("known_errors") or [])
    )
    format_counts = Counter(
        str((row.get("metadata") or {}).get("item_format", "unknown"))
        for row in rows
    )
    difficulty_counts = Counter(
        str((row.get("metadata") or {}).get("difficulty", "unknown"))
        for row in rows
    )

    clean = sum(1 for row in rows if not (row.get("known_errors") or []))
    flawed = len(rows) - clean
    single = sum(1 for row in rows if len(row.get("known_errors") or []) == 1)
    multi = sum(1 for row in rows if len(row.get("known_errors") or []) > 1)

    lines = [
        "## Summary",
        "",
        f"- Total rows: {len(rows)}",
        f"- Clean controls: {clean}",
        f"- Flawed rows: {flawed}",
        f"- Single-label flawed rows: {single}",
        f"- Multi-label flawed rows: {multi}",
        "",
        "## Label Counts",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label, count in sorted(label_counts.items()):
        lines.append(f"| `{label}` | {count} |")

    lines.extend(
        [
            "",
            "## Topic Distribution",
            "",
            "| Topic | Count |",
            "|---|---:|",
        ]
    )
    for topic, count in topic_counts.most_common():
        lines.append(f"| `{topic}` | {count} |")

    lines.extend(
        [
            "",
            "## Format Distribution",
            "",
            "| Item format | Count |",
            "|---|---:|",
        ]
    )
    for item_format, count in format_counts.most_common():
        lines.append(f"| `{item_format}` | {count} |")

    lines.extend(
        [
            "",
            "## Difficulty Distribution",
            "",
            "| Difficulty | Count |",
            "|---|---:|",
        ]
    )
    for difficulty, count in difficulty_counts.most_common():
        lines.append(f"| `{difficulty}` | {count} |")

    return lines


def _build_item_sections(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["## Items", ""]
    for idx, row in enumerate(rows, start=1):
        metadata = row.get("metadata") or {}
        expected_revision = row.get("expected_revision") or {}
        summary = (
            f"{idx}. {row.get('id', '(missing id)')} | "
            f"{'clean' if not (row.get('known_errors') or []) else 'flawed'} | "
            f"{_string_list(row.get('known_errors'))}"
        )
        lines.append(f"<details>")
        lines.append(f"<summary>{summary}</summary>")
        lines.append("")
        lines.append(f"- **Question:** {row.get('question', '')}")
        lines.append(f"- **Response options:** {_string_list(row.get('response_options'))}")
        lines.append(f"- **Known errors:** {_string_list(row.get('known_errors'))}")
        lines.append(f"- **Flawed:** {row.get('is_flawed')}")
        lines.append(f"- **Target concept:** {row.get('target_concept', '')}")
        lines.append(f"- **Topic:** {row.get('topic', '')}")
        lines.append(f"- **Difficulty:** {metadata.get('difficulty', '')}")
        lines.append(f"- **Item format:** {metadata.get('item_format', '')}")
        lines.append(f"- **Split group:** {metadata.get('split_group', '')}")
        lines.append(f"- **Needs manual review:** {metadata.get('needs_manual_review')}")
        lines.append(f"- **Design principles:** {_string_list(metadata.get('design_principles'))}")
        lines.append(f"- **Source refs:** {_string_list(metadata.get('source_refs'))}")
        lines.append(f"- **Chapter refs:** {_string_list(metadata.get('chapter_refs'))}")
        lines.append("")
        lines.append("**Expected revision**")
        lines.append("")
        lines.append(_json_block(expected_revision))
        if metadata:
            lines.append("")
            lines.append("**Metadata**")
            lines.append("")
            lines.append(_json_block(metadata))
        lines.append("")
        lines.append("</details>")
        lines.append("")
    return lines


def export_dataset_markdown(input_path: Path, output_path: Path) -> None:
    rows = _load_jsonl(input_path)
    title = _infer_title(input_path, rows)
    lines = [
        f"# {title}",
        "",
        f"Source dataset: `{input_path}`",
        "",
    ]
    lines.extend(_build_summary(rows))
    lines.append("")
    lines.extend(_build_item_sections(rows))
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument("output_md", nargs="?")
    args = parser.parse_args()

    input_path = Path(args.input_jsonl)
    output_path = (
        Path(args.output_md)
        if args.output_md
        else input_path.with_suffix(".md")
    )
    export_dataset_markdown(input_path, output_path)
    print(f"Wrote markdown dataset view to {output_path}")


if __name__ == "__main__":
    main()
