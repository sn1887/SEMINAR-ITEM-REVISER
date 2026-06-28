from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from item_reviser.constants import DATASET_SCHEMA_VERSION, ERROR_CATEGORIES
from item_reviser.schemas import SurveyItem


DEFAULT_SAMPLING_SEED = 42
SAMPLING_METHOD_FULL_DATASET = "full_dataset"
SAMPLING_METHOD_STRATIFIED = "deterministic_stratified_by_flaw_status"


def _opaque_eval_id(index: int) -> str:
    return f"eval-{index:06d}"


@dataclass
class DatasetMetadata:
    path: str
    hash_algorithm: str
    hash: str
    schema_version: str
    sampling_method: str
    sampling_seed: int
    requested_max_items: int | None
    file_records: int
    returned_records: int
    sampled_opaque_ids: list[str]
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
    sampling_seed: int = DEFAULT_SAMPLING_SEED,
) -> list[SurveyItem]:
    items, _ = load_eval_dataset_with_metadata(
        path,
        max_items=max_items,
        taxonomy_categories=taxonomy_categories,
        sampling_seed=sampling_seed,
    )
    return items


def _truthy_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _is_flawed_for_sampling(item: SurveyItem) -> bool:
    return bool(item.known_errors) or _truthy_bool(item.is_flawed)


def _stratified_sample_counts(strata: dict[str, list[int]], max_items: int) -> dict[str, int]:
    nonempty = {label: indices for label, indices in strata.items() if indices}
    counts = {label: 0 for label in strata}
    if max_items <= 0 or not nonempty:
        return counts

    total_items = sum(len(indices) for indices in nonempty.values())
    if max_items >= total_items:
        return {label: len(indices) for label, indices in strata.items()}

    if max_items < len(nonempty):
        largest_strata = sorted(
            nonempty.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )[:max_items]
        for label, _ in largest_strata:
            counts[label] = 1
        return counts

    counts.update({label: 1 for label in nonempty})
    desired = {
        label: max_items * len(indices) / total_items
        for label, indices in nonempty.items()
    }

    for _ in range(max_items - len(nonempty)):
        eligible = [
            label
            for label, indices in nonempty.items()
            if counts[label] < len(indices)
        ]
        if not eligible:
            break
        label = max(
            eligible,
            key=lambda candidate: (
                desired[candidate] - counts[candidate],
                len(nonempty[candidate]),
                candidate,
            ),
        )
        counts[label] += 1
    return counts


def _sample_items(
    items: list[SurveyItem],
    max_items: int | None,
    *,
    sampling_seed: int,
) -> tuple[list[SurveyItem], str]:
    if max_items is None:
        return items, SAMPLING_METHOD_FULL_DATASET
    if max_items < 0:
        raise ValueError("max_items must be non-negative when provided.")
    if max_items >= len(items):
        return items, SAMPLING_METHOD_FULL_DATASET

    strata = {
        "clean": [
            index
            for index, item in enumerate(items)
            if not _is_flawed_for_sampling(item)
        ],
        "flawed": [
            index
            for index, item in enumerate(items)
            if _is_flawed_for_sampling(item)
        ],
    }
    counts = _stratified_sample_counts(strata, max_items)
    rng = random.Random(sampling_seed)
    selected_indices: list[int] = []
    for label in sorted(strata):
        indices = strata[label]
        count = counts[label]
        if count:
            selected_indices.extend(rng.sample(indices, count))

    selected_index_set = set(selected_indices)
    sampled_items = [
        item
        for index, item in enumerate(items)
        if index in selected_index_set
    ]
    return sampled_items, SAMPLING_METHOD_STRATIFIED


def load_eval_dataset_with_metadata(
    path: str | Path,
    max_items: int | None = None,
    *,
    taxonomy_categories: list[str] | None = None,
    sampling_seed: int = DEFAULT_SAMPLING_SEED,
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
    duplicate_source_ids: set[str] = set()
    unknown_categories: set[str] = set()
    allowed_categories = set(taxonomy_categories or ERROR_CATEGORIES)

    for row, record in enumerate(records, start=1):
        malformed = record.get("_malformed")
        if malformed is not None:
            malformed_rows.append(str(malformed))
            continue

        item = _validate_and_build_item(row, record, errors, missing_required_fields)
        if item.id in seen_ids:
            duplicate_source_ids.add(item.id)
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

    sampling_seed = int(sampling_seed)
    items, sampling_method = _sample_items(
        items,
        max_items,
        sampling_seed=sampling_seed,
    )

    digest = sha256(path.read_bytes()).hexdigest()
    metadata = DatasetMetadata(
        path=str(path),
        hash_algorithm="sha256",
        hash=digest,
        schema_version=DATASET_SCHEMA_VERSION,
        sampling_method=sampling_method,
        sampling_seed=sampling_seed,
        requested_max_items=max_items,
        file_records=file_records,
        returned_records=len(items),
        sampled_opaque_ids=[
            _opaque_eval_id(index)
            for index, _ in enumerate(items, start=1)
        ],
        duplicate_ids=[
            _opaque_eval_id(index)
            for index, item in enumerate(items, start=1)
            if item.id in duplicate_source_ids
        ],
        missing_required_fields=sorted(missing_required_fields),
        malformed_rows=malformed_rows,
        unknown_categories=sorted(unknown_categories),
    )
    return items, metadata
