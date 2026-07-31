import json

from item_reviser.evaluation.dataset import (
    SAMPLING_METHOD_FULL_DATASET,
    SAMPLING_METHOD_STRATIFIED,
    load_eval_dataset_with_metadata,
)

OPTIONS = ["Strongly oppose", "Somewhat oppose", "Neither", "Somewhat support", "Strongly support"]


def _row(item_id: str, *, flawed: bool) -> dict[str, object]:
    question = f"How do you feel about policy {item_id}?"
    if flawed:
        question = f"Don't you agree policy {item_id} is necessary?"
    return {
        "id": item_id,
        "question": question,
        "response_options": OPTIONS,
        "known_errors": ["leading_question"] if flawed else [],
        "is_flawed": flawed,
        "expected_revision": {
            "question": f"To what extent do you support or oppose policy {item_id}?",
            "response_options": OPTIONS,
            "revision_notes": ["Remove leading wording."] if flawed else ["No revision expected."],
        },
        "metadata": {"needs_manual_review": False},
    }


def _write_jsonl(path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row) for row in rows),
        encoding="utf-8",
    )


def test_max_items_uses_seeded_stratified_sample_instead_of_prefix(tmp_path):
    rows = [
        *[_row(f"flawed-{index:02d}", flawed=True) for index in range(1, 9)],
        *[_row(f"clean-{index:02d}", flawed=False) for index in range(1, 3)],
    ]
    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(dataset_path, rows)

    items, metadata = load_eval_dataset_with_metadata(
        dataset_path,
        max_items=5,
        sampling_seed=123,
    )
    repeated_items, repeated_metadata = load_eval_dataset_with_metadata(
        dataset_path,
        max_items=5,
        sampling_seed=123,
    )

    sampled_ids = [item.id for item in items]
    assert sampled_ids == [item.id for item in repeated_items]
    assert metadata.to_dict() == repeated_metadata.to_dict()
    assert sampled_ids != [str(row["id"]) for row in rows[:5]]
    assert sum(1 for item in items if not item.known_errors) == 1
    assert sum(1 for item in items if item.known_errors) == 4
    assert metadata.sampling_method == SAMPLING_METHOD_STRATIFIED
    assert metadata.sampling_seed == 123
    assert metadata.requested_max_items == 5
    assert metadata.returned_records == 5
    assert metadata.sampled_opaque_ids == [
        "eval-000001",
        "eval-000002",
        "eval-000003",
        "eval-000004",
        "eval-000005",
    ]
    assert not set(metadata.sampled_opaque_ids) & set(sampled_ids)


def test_full_dataset_run_preserves_order_and_records_metadata(tmp_path):
    rows = [
        _row("flawed-01", flawed=True),
        _row("clean-01", flawed=False),
        _row("flawed-02", flawed=True),
    ]
    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(dataset_path, rows)

    items, metadata = load_eval_dataset_with_metadata(
        dataset_path,
        max_items=None,
        sampling_seed=987,
    )

    returned_ids = [item.id for item in items]
    assert returned_ids == [str(row["id"]) for row in rows]
    assert metadata.sampling_method == SAMPLING_METHOD_FULL_DATASET
    assert metadata.sampling_seed == 987
    assert metadata.requested_max_items is None
    assert metadata.returned_records == 3
    assert metadata.sampled_opaque_ids == [
        "eval-000001",
        "eval-000002",
        "eval-000003",
    ]
    assert not set(metadata.sampled_opaque_ids) & set(returned_ids)


def test_duplicate_metadata_uses_opaque_ids(tmp_path):
    source_id = "candidate-v1-single-leading-question-001"
    rows = [
        _row(source_id, flawed=True),
        _row(source_id, flawed=True),
    ]
    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(dataset_path, rows)

    items, metadata = load_eval_dataset_with_metadata(dataset_path)

    assert [item.id for item in items] == [source_id, source_id]
    assert metadata.duplicate_ids == ["eval-000001", "eval-000002"]
    assert source_id not in metadata.duplicate_ids
