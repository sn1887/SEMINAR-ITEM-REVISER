from __future__ import annotations

import importlib
import os
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Protocol

from item_reviser.constants import CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY
from item_reviser.schemas import PipelineResult, SurveyItem
from item_reviser.utils import normalize_text


class MetricSetupError(RuntimeError):
    """Raised when a configured library metric cannot be made available."""


class PairwiseBERTScorer(Protocol):
    def score(
        self,
        candidates: list[str],
        references: list[str],
        *,
        batch_size: int | None = None,
    ) -> tuple[Any, Any, Any]: ...


class SARIBackend(Protocol):
    def compute(
        self,
        *,
        sources: list[str],
        predictions: list[str],
        references: list[list[str]],
    ) -> dict[str, float]: ...


@dataclass(frozen=True)
class MetricConfig:
    """Reproducible configuration for the library-backed semantic metrics."""

    bertscore_model_type: str = "distilroberta-base"
    bertscore_num_layers: int | None = 5
    device: str = "cpu"
    batch_size: int = 16
    rescale_with_baseline: bool = False
    language: str = "en"
    cache_path: str = ".metric-cache"
    offline: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_strict_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise ValueError(
        f"evaluator.metric_config.{field_name} must be a boolean true/false value "
        f"(got {value!r})."
    )


def metric_config_from_mapping(config: Mapping[str, Any] | None = None) -> MetricConfig:
    """Build a validated metric configuration from Hydra/dict-style input."""
    raw = dict(config or {})
    aliases = {
        "model_type": "bertscore_model_type",
        "num_layers": "bertscore_num_layers",
        "lang": "language",
    }
    for old_key, new_key in aliases.items():
        if old_key in raw and new_key not in raw:
            raw[new_key] = raw.pop(old_key)
    allowed = set(MetricConfig.__dataclass_fields__)
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ValueError(f"Unknown evaluator.metric_config keys: {', '.join(unknown)}")
    if "bertscore_num_layers" in raw and raw["bertscore_num_layers"] is not None:
        raw["bertscore_num_layers"] = int(raw["bertscore_num_layers"])
    if "batch_size" in raw:
        raw["batch_size"] = int(raw["batch_size"])
    for bool_field in ("rescale_with_baseline", "offline"):
        if bool_field in raw:
            raw[bool_field] = _parse_strict_bool(raw[bool_field], bool_field)
    metric_config = MetricConfig(**raw)
    if metric_config.batch_size < 1:
        raise ValueError("evaluator.metric_config.batch_size must be at least 1.")
    if not metric_config.bertscore_model_type:
        raise ValueError("evaluator.metric_config.bertscore_model_type must not be empty.")
    if not metric_config.language:
        raise ValueError("evaluator.metric_config.language must not be empty.")
    return metric_config


def metric_package_versions() -> dict[str, str]:
    packages = (
        "bert-score",
        "evaluate",
        "numpy",
        "sacrebleu",
        "sacremoses",
        "torch",
        "transformers",
    )
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def bertscore_hash(config: MetricConfig) -> str:
    try:
        from bert_score.utils import get_hash

        return get_hash(
            config.bertscore_model_type,
            config.bertscore_num_layers,
            False,
            config.rescale_with_baseline,
            False,
            False,
        )
    except Exception as exc:
        return f"unavailable:{type(exc).__name__}:{exc}"


def _as_float_list(values: Any) -> list[float]:
    if hasattr(values, "detach"):
        values = values.detach()
    if hasattr(values, "cpu"):
        values = values.cpu()
    if hasattr(values, "tolist"):
        values = values.tolist()
    return [float(value) for value in values]


def _mean_or_none(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _coverage(eligible_items: int, scored_items: int, failed_items: int) -> dict[str, Any]:
    return {
        "eligible_items": eligible_items,
        "scored_items": scored_items,
        "failed_items": failed_items,
        "coverage": scored_items / eligible_items if eligible_items else 0.0,
        "failure_rate": failed_items / eligible_items if eligible_items else 0.0,
    }


def _metric_result(
    values: Sequence[float],
    *,
    eligible_items: int,
    failed_items: int,
    scale: str,
    errors: Sequence[str] = (),
) -> dict[str, Any]:
    scored_items = len(values)
    result = {
        "value": _mean_or_none(values),
        "scale": scale,
        **_coverage(eligible_items, scored_items, failed_items),
    }
    if errors:
        result["errors"] = list(errors)
    return result


def _is_flawed_with_expected_revision(item: SurveyItem) -> bool:
    return bool(item.known_errors) and isinstance(item.expected_revision, dict)


def _expected_question(item: SurveyItem) -> str | None:
    if not _is_flawed_with_expected_revision(item):
        return None
    question = item.expected_revision.get("question")
    if not isinstance(question, str) or not question.strip():
        return None
    return question.strip()


def _expected_options(item: SurveyItem) -> list[str] | None:
    if not _is_flawed_with_expected_revision(item):
        return None
    options = item.expected_revision.get("response_options")
    if not isinstance(options, list):
        return None
    return [str(option) for option in options]


def _exact_question_match(reference: str, prediction: str) -> bool:
    return normalize_text(reference) == normalize_text(prediction)


def _exact_option_match(reference: list[str], prediction: list[str]) -> bool:
    return [normalize_text(option) for option in reference] == [
        normalize_text(option) for option in prediction
    ]


class SemanticRevisionMetrics:
    """One-run metric suite that caches BERTScore and the SARI library module.

    Construct this once per evaluation run, call :meth:`preflight` before model
    generation, and call :meth:`score` exactly once on final results. This keeps
    BERTScore weights loaded once and prevents incremental prediction logging from
    repeatedly rescoring prior rows.
    """

    def __init__(
        self,
        config: MetricConfig | Mapping[str, Any] | None = None,
        *,
        bert_scorer: PairwiseBERTScorer | None = None,
        sari_backend: SARIBackend | None = None,
    ) -> None:
        self.config = (
            config if isinstance(config, MetricConfig) else metric_config_from_mapping(config)
        )
        self._bert_scorer = bert_scorer
        self._sari_backend = sari_backend

    def _configure_cache_environment(self) -> Path:
        cache_path = Path(self.config.cache_path).expanduser().resolve()
        cache_path.mkdir(parents=True, exist_ok=True)
        # BERTScore delegates model resolution to Transformers/HF Hub. Set these
        # before importing the scorer so a fresh Slurm process uses this cache.
        os.environ["HF_HOME"] = str(cache_path)
        os.environ["TRANSFORMERS_CACHE"] = str(cache_path)
        if self.config.offline:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_EVALUATE_OFFLINE"] = "1"
            os.environ["HF_DATASETS_OFFLINE"] = "1"
        else:
            for key in (
                "HF_HUB_OFFLINE",
                "TRANSFORMERS_OFFLINE",
                "HF_EVALUATE_OFFLINE",
                "HF_DATASETS_OFFLINE",
            ):
                os.environ.pop(key, None)
        return cache_path

    def _ensure_bert_scorer(self) -> PairwiseBERTScorer:
        if self._bert_scorer is not None:
            return self._bert_scorer
        cache_path = self._configure_cache_environment()
        try:
            from bert_score import BERTScorer

            self._bert_scorer = BERTScorer(
                model_type=self.config.bertscore_model_type,
                num_layers=self.config.bertscore_num_layers,
                batch_size=self.config.batch_size,
                device=self.config.device,
                lang=self.config.language,
                rescale_with_baseline=self.config.rescale_with_baseline,
            )
        except Exception as exc:
            raise MetricSetupError(
                "Unable to load BERTScore checkpoint "
                f"{self.config.bertscore_model_type!r} on {self.config.device!r}. "
                f"Ensure its weights are available in {cache_path} before offline "
                "Slurm execution, or set evaluator.metric_config.offline=false for "
                "a connected preflight."
            ) from exc
        return self._bert_scorer

    def _ensure_sari_backend(self) -> SARIBackend:
        if self._sari_backend is not None:
            return self._sari_backend
        cache_path = self._configure_cache_environment()
        try:
            # The repository's canonical entry point is scripts/evaluate.py. When
            # that directory is first on sys.path, a normal `import evaluate`
            # would import the entry point instead of Hugging Face Evaluate.
            loaded = sys.modules.get("evaluate")
            if not callable(getattr(loaded, "load", None)):
                sys.modules.pop("evaluate", None)
                scripts_dir = Path(__file__).resolve().parents[3] / "scripts"
                original_path = list(sys.path)
                sys.path[:] = [
                    entry for entry in sys.path if Path(entry or ".").resolve() != scripts_dir
                ]
                try:
                    loaded = importlib.import_module("evaluate")
                finally:
                    sys.path[:] = original_path
            if not callable(getattr(loaded, "load", None)):
                raise ImportError("Hugging Face Evaluate does not expose evaluate.load")
            if hasattr(loaded, "config"):
                loaded.config.HF_EVALUATE_OFFLINE = bool(self.config.offline)
            self._sari_backend = loaded.load("sari", cache_dir=str(cache_path))
        except Exception as exc:
            raise MetricSetupError(
                "Unable to load Evaluate's SARI metric module. Cache it before an "
                f"offline run with `evaluate.load('sari', cache_dir={str(cache_path)!r})`; "
                "the module also requires sacremoses."
            ) from exc
        return self._sari_backend

    def preflight(self) -> dict[str, Any]:
        """Eagerly load metric resources once, before expensive LLM generation."""
        self._ensure_bert_scorer()
        self._ensure_sari_backend()
        return self.metadata()

    def _bertscore_hash(self) -> str:
        if self._bert_scorer is not None:
            scorer_hash = getattr(self._bert_scorer, "hash", None)
            if isinstance(scorer_hash, str):
                return scorer_hash
        return bertscore_hash(self.config)

    def metadata(self) -> dict[str, Any]:
        return {
            "metric_config": self.config.to_dict(),
            "package_versions": metric_package_versions(),
            "bertscore_hash": self._bertscore_hash(),
        }

    def _bertscore_f1(self, candidates: list[str], references: list[str]) -> list[float]:
        if len(candidates) != len(references):
            raise ValueError("BERTScore candidates and references must have the same length.")
        if not candidates:
            return []
        _, _, f1 = self._ensure_bert_scorer().score(
            candidates,
            references,
            batch_size=self.config.batch_size,
        )
        scores = _as_float_list(f1)
        if len(scores) != len(candidates):
            raise RuntimeError("BERTScore returned an unexpected number of F1 values.")
        return scores

    def score(self, items: Sequence[SurveyItem], results: Sequence[PipelineResult]) -> dict[str, Any]:
        """Score final gold-flawed revisions; clean controls are intentionally excluded."""
        if len(items) != len(results):
            raise ValueError("items and results must have the same length")

        pairs = list(zip(items, results, strict=True))
        question_pairs = [(item, result, _expected_question(item)) for item, result in pairs]
        question_pairs = [(item, result, reference) for item, result, reference in question_pairs if reference]
        option_pairs = [(item, result, _expected_options(item)) for item, result in pairs]
        option_pairs = [(item, result, reference) for item, result, reference in option_pairs if reference is not None]

        question_eligible = len(question_pairs)
        question_failed = sum(result.failed() for _, result, _ in question_pairs)
        question_values: list[float] = []
        question_errors: list[str] = []
        scoreable_questions = [pair for pair in question_pairs if not pair[1].failed()]
        if scoreable_questions:
            try:
                question_values = self._bertscore_f1(
                    [result.revised_item.question for _, result, _ in scoreable_questions],
                    [reference for _, _, reference in scoreable_questions],
                )
            except Exception as exc:
                question_failed += len(scoreable_questions)
                question_errors.append(f"BERTScore question batch failed: {type(exc).__name__}: {exc}")

        sari_eligible = question_eligible
        sari_failed = sum(result.failed() for _, result, _ in question_pairs)
        sari_values: list[float] = []
        sari_errors: list[str] = []
        scoreable_sari = [pair for pair in question_pairs if not pair[1].failed()]
        if scoreable_sari:
            try:
                sari_score = self._ensure_sari_backend().compute(
                    sources=[item.question for item, _, _ in scoreable_sari],
                    predictions=[result.revised_item.question for _, result, _ in scoreable_sari],
                    references=[[reference] for _, _, reference in scoreable_sari],
                )["sari"]
                sari_values = [float(sari_score)] * len(scoreable_sari)
            except Exception as exc:
                sari_failed += len(scoreable_sari)
                sari_errors.append(f"SARI batch failed: {type(exc).__name__}: {exc}")

        diagnostic_eligible = [
            (item, result)
            for item, result in pairs
            if _expected_question(item) is not None or _expected_options(item) is not None
        ]
        diagnostic_successful = [
            (item, result) for item, result in diagnostic_eligible if not result.failed()
        ]

        semantic_failure_ids = {
            item.id for item, result, _ in question_pairs if result.failed()
        }
        if question_errors:
            semantic_failure_ids.update(item.id for item, _, _ in scoreable_questions)
        if sari_errors:
            semantic_failure_ids.update(item.id for item, _, _ in scoreable_sari)
        semantic_failed = len(semantic_failure_ids)
        semantic_scored = question_eligible - semantic_failed

        exact_question_pairs = [pair for pair in question_pairs if not pair[1].failed()]
        exact_option_pairs = [pair for pair in option_pairs if not pair[1].failed()]
        complete_pairs = [
            (item, result, question, options)
            for item, result in pairs
            if (question := _expected_question(item)) is not None
            and (options := _expected_options(item)) is not None
            and not result.failed()
        ]
        diagnostics = {
            "exact_question_match_rate": (
                sum(_exact_question_match(reference, result.revised_item.question) for _, result, reference in exact_question_pairs)
                / len(exact_question_pairs)
                if exact_question_pairs
                else None
            ),
            "exact_option_match_rate": (
                sum(_exact_option_match(reference, result.revised_item.response_options) for _, result, reference in exact_option_pairs)
                / len(exact_option_pairs)
                if exact_option_pairs
                else None
            ),
            "exact_revision_rate": (
                sum(
                    _exact_question_match(question, result.revised_item.question)
                    and _exact_option_match(options, result.revised_item.response_options)
                    for _, result, question, options in complete_pairs
                )
                / len(complete_pairs)
                if complete_pairs
                else None
            ),
            "revision_changed_rate": (
                sum(result.revised_item.changed for _, result in diagnostic_successful)
                / len(diagnostic_successful)
                if diagnostic_successful
                else None
            ),
            "exact_question_match_eligible_items": len(exact_question_pairs),
            "exact_option_match_eligible_items": len(exact_option_pairs),
            "exact_revision_eligible_items": len(complete_pairs),
            "revision_changed_eligible_items": len(diagnostic_successful),
        }
        return {
            "metric_role": "supporting_revision_metrics",
            "scope": "gold_flawed_items_with_valid_expected_questions",
            "excluded_clean_items": sum(not item.known_errors for item, _ in pairs),
            "question_bertscore_f1": _metric_result(
                question_values,
                eligible_items=question_eligible,
                failed_items=question_failed,
                scale="0_to_1",
                errors=question_errors,
            ),
            "sari": _metric_result(
                sari_values,
                eligible_items=sari_eligible,
                failed_items=sari_failed,
                scale="0_to_100",
                errors=sari_errors,
            ),
            **_coverage(question_eligible, semantic_scored, semantic_failed),
            **diagnostics,
            **self.metadata(),
        }


def _category_weight(category: str, weights: dict[str, float] | None) -> float:
    if weights is None:
        return 0.0
    return float(weights.get(category, 0.5))


def compute_detection_metrics(
    items: list[SurveyItem],
    results: list[PipelineResult],
    *,
    use_severity_weighting: bool = False,
    category_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute detection-only metrics; semantic revision metrics are scored separately."""
    if len(items) != len(results):
        raise ValueError("items and results must have same length")

    tp = fp = fn = 0
    exact = 0
    clean_total = clean_false_positive = clean_changed = 0
    manual_total = manual_changed = manual_clean_changes = 0
    weighted_tp = weighted_fp = weighted_fn = 0.0
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    severity_weights = CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY if use_severity_weighting else None
    if category_weights is not None:
        severity_weights = dict(category_weights)

    for item, result in zip(items, results, strict=True):
        gold = set(item.known_errors)
        pred = set(result.predicted_categories())
        failed = result.failed()
        if not failed and gold == pred:
            exact += 1
        for category in pred & gold:
            tp += 1
            weighted_tp += _category_weight(category, severity_weights)
            by_category[category]["tp"] += 1
        for category in pred - gold:
            fp += 1
            weighted_fp += _category_weight(category, severity_weights)
            by_category[category]["fp"] += 1
        for category in gold - pred:
            fn += 1
            weighted_fn += _category_weight(category, severity_weights)
            by_category[category]["fn"] += 1
        if not gold:
            clean_total += 1
            clean_false_positive += bool(pred)
            clean_changed += result.revised_item.changed
        if item.needs_manual_review():
            manual_total += 1
            manual_changed += result.revised_item.changed
            manual_clean_changes += bool(not gold and result.revised_item.changed)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    weighted_precision = weighted_tp / (weighted_tp + weighted_fp) if weighted_tp + weighted_fp else 0.0
    weighted_recall = weighted_tp / (weighted_tp + weighted_fn) if weighted_tp + weighted_fn else 0.0
    weighted_f1 = (
        2 * weighted_precision * weighted_recall / (weighted_precision + weighted_recall)
        if weighted_precision + weighted_recall
        else 0.0
    )
    return {
        "num_items": len(items),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match": exact / len(items) if items else 0.0,
        "clean_items": clean_total,
        "false_positive_rate_on_clean_items": clean_false_positive / clean_total if clean_total else 0.0,
        "overcorrection_rate": clean_changed / clean_total if clean_total else 0.0,
        "manual_review": {
            "items_flagged_for_review": manual_total,
            "items_flagged_and_changed": manual_changed,
            "items_flagged_change_rate": manual_changed / manual_total if manual_total else 0.0,
            "flagged_clean_items_changed": manual_clean_changes,
            "flagged_clean_items_change_rate": manual_clean_changes / manual_total if manual_total else 0.0,
        },
        "metric_roles": {
            "primary_detection": [
                "precision", "recall", "f1", "exact_match",
                "false_positive_rate_on_clean_items", "overcorrection_rate",
            ],
            "supporting_revision": [
                "revision_quality.question_bertscore_f1",
                "revision_quality.sari",
                "revision_quality.exact_question_match_rate",
                "revision_quality.exact_option_match_rate",
                "revision_quality.exact_revision_rate",
                "revision_quality.revision_changed_rate",
            ],
        },
        "severity_weighted": {
            "enabled": bool(use_severity_weighting),
            "precision": weighted_precision,
            "recall": weighted_recall,
            "f1": weighted_f1,
            "tp_weighted": weighted_tp,
            "fp_weighted": weighted_fp,
            "fn_weighted": weighted_fn,
            "category_weights": CATEGORY_SEVERITY_WEIGHTS_BY_CATEGORY if use_severity_weighting else {},
        },
        "by_category": {category: dict(counts) for category, counts in sorted(by_category.items())},
    }
