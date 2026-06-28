from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from omegaconf import DictConfig, OmegaConf

from item_reviser.models.base import BaseLLM
from item_reviser.models.hf_local import HuggingFaceLocalModel
from item_reviser.models.openai_compatible import OpenAICompatibleModel


def _coerce_cfg(cfg: object) -> dict[str, Any]:
    if cfg is None:
        raise ValueError("A model config is required for LLM-agent evaluation.")
    if isinstance(cfg, str):
        return {"backend": cfg}
    if isinstance(cfg, dict):
        return dict(cfg)
    if isinstance(cfg, DictConfig):
        return dict(OmegaConf.to_container(cfg, resolve=True))
    if hasattr(cfg, "to_container"):
        return cfg.to_container(resolve=True)  # type: ignore[call-arg]
    return dict(vars(cfg))


def _nested_mapping(cfg: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = cfg.get(key, {})
    if isinstance(value, Mapping):
        return value
    return {}


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _nested_bool(
    cfg: Mapping[str, Any],
    nested: Mapping[str, Any],
    key: str,
    default: bool,
) -> bool:
    value = nested.get(key, cfg.get(key, default))
    return _coerce_bool(value, default)


def _get_decoding_value(
    cfg: Mapping[str, Any],
    decoding: Mapping[str, Any],
    key: str,
    default: Any,
) -> Any:
    value = decoding.get(key, cfg.get(key, default))
    return default if value is None else value


def _optional_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


def _optional_positive_float(value: Any) -> float | None:
    if value is None:
        return None
    parsed = float(value)
    return parsed if parsed > 0 else None


def _sync_hf_local_runtime_config(cfg: object, model: HuggingFaceLocalModel) -> None:
    if not isinstance(cfg, DictConfig):
        return
    OmegaConf.update(
        cfg,
        "chat_template.enable_thinking",
        bool(model.enable_thinking),
        force_add=True,
    )
    OmegaConf.update(
        cfg,
        "chat_template.supports_enable_thinking",
        bool(model.supports_enable_thinking),
        force_add=True,
    )


def build_model(cfg: object | None) -> BaseLLM:
    cfg_data = _coerce_cfg(cfg)
    backend = str(
        cfg_data.get("backend")
        or cfg_data.get("type")
        or cfg_data.get("name")
        or "hf_local"
    )

    if backend == "hf_local":
        model_path = str(cfg_data.get("model_path", "")).strip()
        if not model_path:
            raise ValueError("hf_local backend requires model_path.")
        decoding_cfg = _nested_mapping(cfg_data, "decoding")
        chat_template_cfg = _nested_mapping(cfg_data, "chat_template")
        top_k = _get_decoding_value(cfg_data, decoding_cfg, "top_k", None)
        repetition_penalty = _get_decoding_value(
            cfg_data, decoding_cfg, "repetition_penalty", None
        )
        model = HuggingFaceLocalModel(
            model_path=model_path,
            trust_remote_code=bool(cfg_data.get("trust_remote_code", False)),
            device_map=cfg_data.get("device_map"),
            torch_dtype=str(cfg_data.get("torch_dtype", "auto")),
            enable_thinking=_nested_bool(
                cfg_data,
                chat_template_cfg,
                "enable_thinking",
                False,
            ),
            decoding_method=str(
                _get_decoding_value(cfg_data, decoding_cfg, "method", "greedy")
            ),
            max_new_tokens=int(
                _get_decoding_value(cfg_data, decoding_cfg, "max_new_tokens", 768)
            ),
            temperature=float(
                _get_decoding_value(cfg_data, decoding_cfg, "temperature", 0.0)
            ),
            top_p=float(_get_decoding_value(cfg_data, decoding_cfg, "top_p", 1.0)),
            top_k=_optional_positive_int(top_k),
            num_beams=int(_get_decoding_value(cfg_data, decoding_cfg, "num_beams", 1)),
            repetition_penalty=_optional_positive_float(repetition_penalty),
            timeout_seconds=float(cfg_data.get("timeout_seconds", 120.0)),
        )
        _sync_hf_local_runtime_config(cfg, model)
        return model

    if backend == "openai_compatible":
        model_name = str(cfg_data.get("model_name", "")).strip()
        if not model_name:
            raise ValueError("openai_compatible backend requires model_name.")
        return OpenAICompatibleModel(
            base_url=str(cfg_data.get("base_url", "")).strip(),
            model_name=model_name,
            api_key=cfg_data.get("api_key"),
            api_key_env=str(cfg_data.get("api_key_env", "OPENAI_API_KEY")),
            max_new_tokens=int(cfg_data.get("max_new_tokens", 768)),
            temperature=float(cfg_data.get("temperature", 0.0)),
            timeout_seconds=float(cfg_data.get("timeout_seconds", 120.0)),
        )

    raise ValueError(f"Unsupported model backend '{backend}'.")
