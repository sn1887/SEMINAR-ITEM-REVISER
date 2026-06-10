from __future__ import annotations

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
        self._pipeline = None
        self._tokenizer = None

    def _load_pipeline(self) -> None:
        if self._pipeline is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        dtype = _parse_torch_dtype(self.torch_dtype)
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=self.trust_remote_code,
        )
        model_kwargs: dict[str, Any] = {
            "trust_remote_code": self.trust_remote_code,
            "torch_dtype": dtype,
        }
        if self.device_map:
            model_kwargs["device_map"] = self.device_map
        model = AutoModelForCausalLM.from_pretrained(self.model_path, **model_kwargs)
        self._tokenizer = tokenizer
        self._pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
        )

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
            "eos_token_id": self._tokenizer.eos_token_id
            if self._tokenizer is not None
            else None,
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

        outputs = self._pipeline(prompt, **generation_kwargs)
        if not outputs:
            return ""
        text = outputs[0].get("generated_text", "")
        if text.startswith(prompt):
            text = text[len(prompt) :]
        return text.strip()
