from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from item_reviser.models.base import BaseLLM


def _parse_torch_dtype(raw: str | None) -> Any:
    if raw in (None, "", "auto"):
        return "auto"
    import torch  # Imported lazily to avoid forcing torch dependency for non-hf paths.

    dtype_name = raw.lower().replace("_", "")
    if dtype_name in {"fp16", "float16"}:
        return torch.float16
    if dtype_name in {"bf16", "bfloat16"}:
        return torch.bfloat16
    if dtype_name in {"fp32", "float32"}:
        return torch.float32
    if dtype_name in {"fp64", "float64"}:
        return torch.float64
    raise ValueError(f"Unsupported torch dtype: {raw}")


def _chat_template_supports_enable_thinking(model_path: str) -> bool:
    path = Path(model_path)
    if not path.exists():
        return False

    template_texts: list[str] = []
    tokenizer_config = path / "tokenizer_config.json"
    if tokenizer_config.exists():
        try:
            data = json.loads(tokenizer_config.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        chat_template = data.get("chat_template")
        if isinstance(chat_template, str):
            template_texts.append(chat_template)
        elif isinstance(chat_template, list):
            for entry in chat_template:
                if not isinstance(entry, dict):
                    continue
                template = entry.get("template")
                if isinstance(template, str):
                    template_texts.append(template)

    jinja_template = path / "chat_template.jinja"
    if jinja_template.exists():
        try:
            template_texts.append(jinja_template.read_text(encoding="utf-8"))
        except OSError:
            pass

    return any("enable_thinking" in template for template in template_texts)


class HuggingFaceLocalModel(BaseLLM):
    backend_name = "hf_local"

    def __init__(
        self,
        model_path: str,
        *,
        trust_remote_code: bool = False,
        device_map: str | None = None,
        torch_dtype: str | None = "auto",
        decoding_method: str = "greedy",
        temperature: float | None = 0.0,
        top_p: float | None = 1.0,
        top_k: int | None = None,
        num_beams: int | None = 1,
        repetition_penalty: float | None = None,
        max_new_tokens: int | None = 768,
        timeout_seconds: float | None = None,
        enable_thinking: bool = False,
    ) -> None:
        super().__init__(
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
        )
        self.model_path = model_path
        self.trust_remote_code = trust_remote_code
        self.device_map = device_map
        self.torch_dtype = torch_dtype
        self.decoding_method = decoding_method
        self.top_p = top_p
        self.top_k = top_k
        self.num_beams = num_beams
        self.repetition_penalty = repetition_penalty
        self.requested_enable_thinking = bool(enable_thinking)
        self.supports_enable_thinking = _chat_template_supports_enable_thinking(model_path)
        self.enable_thinking = self.requested_enable_thinking and self.supports_enable_thinking
        self._model = None
        self._tokenizer = None
        self._processor = None
        self._is_multimodal = False

    def _load_pipeline(self) -> None:
        if self._model is not None:
            return
        from transformers import AutoConfig

        config = AutoConfig.from_pretrained(
            self.model_path,
            trust_remote_code=self.trust_remote_code,
        )
        dtype = _parse_torch_dtype(self.torch_dtype)
        model_kwargs: dict[str, Any] = {
            "trust_remote_code": self.trust_remote_code,
            "torch_dtype": dtype,
        }
        if self.device_map:
            model_kwargs["device_map"] = self.device_map
        architecture = (getattr(config, "architectures", []) or [""])[0]
        model_type = getattr(config, "model_type", "")

        if model_type == "qwen3_5" or "ConditionalGeneration" in architecture:
            from transformers import AutoModelForImageTextToText, AutoProcessor

            self._processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=self.trust_remote_code,
            )
            self._model = AutoModelForImageTextToText.from_pretrained(
                self.model_path,
                **model_kwargs,
            )
            self._is_multimodal = True
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=self.trust_remote_code,
        )
        self._model = AutoModelForCausalLM.from_pretrained(self.model_path, **model_kwargs)
        self._is_multimodal = False

    def _input_device(self) -> Any:
        if self._model is None:
            raise RuntimeError("Model has not been loaded.")
        return next(self._model.parameters()).device

    def _eos_token_id(self) -> int | None:
        if self._tokenizer is not None:
            return self._tokenizer.eos_token_id
        if self._processor is not None and hasattr(self._processor, "tokenizer"):
            return self._processor.tokenizer.eos_token_id
        return None

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        num_beams: int | None = None,
        repetition_penalty: float | None = None,
        decoding_method: str | None = None,
        **kwargs,
    ) -> str:
        _ = timeout_seconds, kwargs
        self._load_pipeline()

        max_tokens = (
            max_new_tokens if max_new_tokens is not None else (self.max_new_tokens or 256)
        )
        method = (decoding_method or self.decoding_method or "greedy").strip().lower()
        effective_temperature = temperature if temperature is not None else self.temperature
        effective_top_p = top_p if top_p is not None else self.top_p
        effective_top_k = top_k if top_k is not None else self.top_k
        effective_num_beams = num_beams if num_beams is not None else self.num_beams
        effective_repetition_penalty = (
            repetition_penalty
            if repetition_penalty is not None
            else self.repetition_penalty
        )

        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": max_tokens,
            "eos_token_id": self._eos_token_id(),
        }

        if method in {"greedy", "deterministic"}:
            generation_kwargs["do_sample"] = False
            generation_kwargs["num_beams"] = 1
        elif method in {"sample", "sampling"}:
            generation_kwargs["do_sample"] = True
            generation_kwargs["temperature"] = (
                effective_temperature
                if effective_temperature and effective_temperature > 0
                else 0.7
            )
            generation_kwargs["top_p"] = effective_top_p if effective_top_p is not None else 1.0
            if effective_top_k is not None:
                generation_kwargs["top_k"] = effective_top_k
        elif method in {"beam", "beam_search"}:
            generation_kwargs["do_sample"] = False
            generation_kwargs["num_beams"] = max(int(effective_num_beams or 4), 2)
        elif method in {"beam_sample", "beam_sampling"}:
            generation_kwargs["do_sample"] = True
            generation_kwargs["num_beams"] = max(int(effective_num_beams or 4), 2)
            generation_kwargs["temperature"] = (
                effective_temperature
                if effective_temperature and effective_temperature > 0
                else 0.7
            )
            generation_kwargs["top_p"] = effective_top_p if effective_top_p is not None else 1.0
            if effective_top_k is not None:
                generation_kwargs["top_k"] = effective_top_k
        else:
            raise ValueError(
                "Unsupported decoding_method. Use one of: greedy, sampling, "
                "beam_search, beam_sample."
            )

        if effective_repetition_penalty is not None:
            generation_kwargs["repetition_penalty"] = effective_repetition_penalty

        if self._is_multimodal:
            messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ]
            template_kwargs: dict[str, Any] = {
                "tokenize": False,
                "add_generation_prompt": True,
            }
            if self.supports_enable_thinking:
                template_kwargs["enable_thinking"] = self.enable_thinking
            rendered_prompt = self._processor.apply_chat_template(
                messages,
                **template_kwargs,
            )
            inputs = self._processor(text=[rendered_prompt], return_tensors="pt")
        else:
            inputs = self._tokenizer(prompt, return_tensors="pt")

        device = self._input_device()
        inputs = {
            key: value.to(device) if hasattr(value, "to") else value
            for key, value in inputs.items()
        }
        outputs = self._model.generate(**inputs, **generation_kwargs)
        prompt_length = inputs["input_ids"].shape[1]
        generated_ids = outputs[:, prompt_length:]

        if self._is_multimodal:
            text = self._processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]
        else:
            text = self._tokenizer.batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]
        return text.strip()
