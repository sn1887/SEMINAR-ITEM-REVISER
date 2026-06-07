from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from item_reviser.constants import DATASET_SCHEMA_VERSION, ERROR_CATEGORIES
from item_reviser.schemas import SurveyItem


@dataclass
class DatasetMetadata:
    path: str
    hash_algorithm: str
    hash: str
    schema_version: str
    requested_max_items: int | None
    file_records: int
    returned_records: int
    duplicate_ids: list[str]
    missing_required_fields: list[str]
    malformed_rows: list[str]
    unknown_categories: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _coerce_string_list(
    value: object, field_name: str, row: int, errors: list[str]
) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value]
    if value is None:
        return []
    errors.append(f"row {row}: field '{field_name}' must be a list")
    return []


def _coerce_dict(value: object, field_name: str, row: int, errors: list[str]) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    errors.append(f"row {row}: field '{field_name}' must be an object")
    return {}


def _validate_and_build_item(
    row: int,
    record: dict[str, object],
    errors: list[str],
    missing_fields: set[str],
) -> SurveyItem:
    required = ("id", "question", "response_options", "known_errors", "expected_revision", "metadata")
    for field in required:
        if field not in record:
            errors.append(f"row {row}: missing required field '{field}'")
            missing_fields.add(field)

    raw_known_errors = record.get("known_errors", [])
    if not isinstance(raw_known_errors, list):
        errors.append(f"row {row}: field 'known_errors' must be a list")
        raw_known_errors = []

    known_errors = [str(item).strip() for item in raw_known_errors if str(item).strip()]
    item_payload = {
        "id": str(record.get("id", "")).strip(),
        "question": str(record.get("question", "")).strip(),
        "response_options": _coerce_string_list(
            record.get("response_options"), "response_options", row, errors
        ),
        "target_concept": record.get("target_concept"),
        "topic": record.get("topic"),
        "known_errors": known_errors,
        "is_flawed": record.get("is_flawed"),
        "expected_revision": _coerce_dict(record.get("expected_revision"), "expected_revision", row, errors),
        "metadata": _coerce_dict(record.get("metadata"), "metadata", row, errors),
    }

    if not item_payload["id"]:
        errors.append(f"row {row}: field 'id' must be non-empty")
    if not item_payload["question"]:
        errors.append(f"row {row}: field 'question' must be non-empty")

    return SurveyItem.from_dict(item_payload)


def load_eval_dataset(
    path: str | Path,
    max_items: int | None = None,
    *,
    taxonomy_categories: list[str] | None = None,
) -> list[SurveyItem]:
    items, _ = load_eval_dataset_with_metadata(
        path,
        max_items=max_items,
        taxonomy_categories=taxonomy_categories,
    )
    return items


def load_eval_dataset_with_metadata(
    path: str | Path,
    max_items: int | None = None,
    *,
    taxonomy_categories: list[str] | None = None,
) -> tuple[list[SurveyItem], DatasetMetadata]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    records: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as f:
        for row, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                records.append({"_malformed": f"row {row}: invalid JSON ({exc})"})
                continue
            if not isinstance(record, dict):
                records.append({"_malformed": f"row {row}: record is not an object"})
                continue
            records.append(record)

    file_records = len(records)
    errors: list[str] = []
    malformed_rows: list[str] = []
    missing_required_fields: set[str] = set()
    items: list[SurveyItem] = []
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    unknown_categories: set[str] = set()
    allowed_categories = set(taxonomy_categories or ERROR_CATEGORIES)

    for row, record in enumerate(records, start=1):
        malformed = record.get("_malformed")
        if malformed is not None:
            malformed_rows.append(str(malformed))
            continue

        item = _validate_and_build_item(row, record, errors, missing_required_fields)
        if item.id in seen_ids:
            duplicate_ids.add(item.id)
        else:
            seen_ids.add(item.id)

        for category in item.known_errors:
            if category not in allowed_categories:
                unknown_categories.add(category)
        items.append(item)

    if errors or malformed_rows or unknown_categories:
        details = []
        if malformed_rows:
            details.extend(malformed_rows)
        if errors:
            details.extend(errors)
        if unknown_categories:
            details.extend(
                [f"row unknown: unknown categories found {', '.join(sorted(unknown_categories))}"]
            )
        raise ValueError("Dataset validation failed:\\n" + "\\n".join(details))

    if max_items is not None:
        items = items[:max_items]

    digest = sha256(path.read_bytes()).hexdigest()
    metadata = DatasetMetadata(
        path=str(path),
        hash_algorithm="sha256",
        hash=digest,
        schema_version=DATASET_SCHEMA_VERSION,
        requested_max_items=max_items,
        file_records=file_records,
        returned_records=len(items),
        duplicate_ids=sorted(duplicate_ids),
        missing_required_fields=sorted(missing_required_fields),
        malformed_rows=malformed_rows,
        unknown_categories=sorted(unknown_categories),
    )
    return items, metadata
