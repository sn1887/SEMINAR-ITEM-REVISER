from __future__ import annotations

import os
import time

import requests

from item_reviser.models.base import BaseLLM


class OpenAICompatibleModel(BaseLLM):
    backend_name = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        model_name: str,
        *,
        api_key_env: str = "OPENAI_API_KEY",
        temperature: float | None = 0.0,
        top_p: float | None = 1.0,
        timeout_seconds: float | None = 120.0,
        max_new_tokens: int | None = 768,
        api_key: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
        )
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.api_key_env = api_key_env
        self.api_key = api_key or os.getenv(api_key_env, "")
        self.top_p = top_p if top_p is not None else 1.0
        self.extra_client_kwargs = kwargs

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
        **kwargs,
    ) -> str:
        _ = kwargs
        endpoint = f"{self.base_url}/chat/completions"
        temperature_to_use = temperature if temperature is not None else self.temperature
        top_p_to_use = top_p if top_p is not None else self.top_p
        max_tokens_to_use = max_new_tokens if max_new_tokens is not None else self.max_new_tokens
        request_timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature_to_use,
            "top_p": top_p_to_use,
            "max_tokens": max_tokens_to_use,
        }

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=request_timeout,
                    **self.extra_client_kwargs,
                )
                response.raise_for_status()
                data = response.json()
            except (requests.Timeout, requests.RequestException) as exc:
                last_error = exc
            else:
                if "error" in data:
                    last_error = RuntimeError(str(data["error"]))
                else:
                    choices = data.get("choices", [])
                    if not choices:
                        last_error = RuntimeError("No choices returned by API server.")
                    else:
                        choice = choices[0]
                        message = choice.get("message", {})
                        content = message.get("content")
                        if isinstance(content, str) and content.strip():
                            return content.strip()
                        text = choice.get("text")
                        if isinstance(text, str) and text.strip():
                            return text.strip()
                        last_error = RuntimeError("Choice content is empty.")

            if attempt >= max_retries:
                break
            backoff = retry_backoff_seconds * (attempt**1.5)
            time.sleep(backoff)

        if last_error is None:
            raise RuntimeError("OpenAI-compatible request failed without a concrete response error.")
        raise last_error
