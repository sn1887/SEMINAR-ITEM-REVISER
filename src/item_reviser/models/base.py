from __future__ import annotations

import json
import math
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class LLMError(RuntimeError):
    """Base class for LLM wrapper errors."""


class LLMOutputError(LLMError):
    """Raised when model output cannot be interpreted as structured text."""


class LLMOutputParseError(LLMOutputError):
    """Raised when a model output cannot be parsed as JSON."""


class LLMOutputSchemaError(LLMOutputError):
    """Raised when a parsed output does not match an expected schema."""


REVISER_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["question", "response_options", "revision_notes", "changed"],
    "additionalProperties": False,
    "properties": {
        "question": {"type": "string"},
        "response_options": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0,
        },
        "revision_notes": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0,
        },
        "changed": {"type": "boolean"},
    },
}


CHECKER_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["errors"],
    "additionalProperties": False,
    "properties": {
        "errors": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "required": ["category", "severity", "explanation"],
                "additionalProperties": True,
                "properties": {
                    "category": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "explanation": {"type": "string"},
                    "evidence": {"type": ["string", "null"]},
                    "suggestion": {"type": ["string", "null"]},
                    "checker": {"type": ["string", "null"]},
                },
            },
        },
    },
}


def _extract_json_snippet(text: str) -> str:
    trimmed = (text or "").strip()
    if not trimmed:
        raise LLMOutputParseError("Model output is empty.")

    fence_match = re.search(r"```(?:json)?\\s*(.*?)\\s*```", trimmed, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        body = fence_match.group(1).strip()
        if body:
            return body

    def _find_balanced(source: str, start_idx: int, open_ch: str, close_ch: str) -> str:
        depth = 0
        in_string = False
        escape = False
        for idx in range(start_idx, len(source)):
            char = source[idx]
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = in_string
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == open_ch:
                depth += 1
            elif char == close_ch:
                depth -= 1
                if depth == 0:
                    return source[start_idx : idx + 1]
        raise LLMOutputParseError("Could not find complete JSON payload in model output.")

    first_obj = trimmed.find("{")
    first_arr = trimmed.find("[")
    candidates: list[tuple[int, str, str]] = []
    if first_obj != -1:
        candidates.append((first_obj, "{", "}"))
    if first_arr != -1:
        candidates.append((first_arr, "[", "]"))
    if not candidates:
        raise LLMOutputParseError("No JSON-like token found in model output.")

    start, open_ch, close_ch = min(candidates, key=lambda x: x[0])
    return _find_balanced(trimmed, start, open_ch, close_ch)


def parse_json_output(text: str) -> Any:
    raw = _extract_json_snippet(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMOutputParseError(f"Invalid JSON: {exc}") from exc


def _validate_schema(data: Any, schema: Mapping[str, Any], path: str = "") -> None:
    def _prefix(name: str) -> str:
        return f"{path}.{name}" if path else name

    if not isinstance(schema, Mapping):
        return

    if "enum" in schema and data not in schema["enum"]:
        raise LLMOutputSchemaError(f"{path or 'value'} must be one of {schema['enum']}.")

    expected_type = schema.get("type")
    if isinstance(expected_type, list | tuple | set):
        for candidate_type in expected_type:
            candidate_schema = dict(schema)
            candidate_schema["type"] = candidate_type
            try:
                _validate_schema(data, candidate_schema, path)
                return
            except LLMOutputSchemaError:
                continue
        choices = ", ".join(str(item) for item in expected_type)
        raise LLMOutputSchemaError(
            f"{path or 'value'} must match one of the allowed types: {choices}."
        )

    if expected_type == "object":
        if not isinstance(data, Mapping):
            raise LLMOutputSchemaError(f"{path or 'value'} must be an object.")
        required_fields = schema.get("required", [])
        for required in required_fields:
            if required not in data:
                raise LLMOutputSchemaError(
                    f"{_prefix(str(required))} is required by schema."
                )
        properties = schema.get("properties", {})
        additional_allowed = schema.get("additionalProperties", True)
        for key, value in data.items():
            if key not in properties and not additional_allowed:
                raise LLMOutputSchemaError(
                    f"Unexpected key '{key}' at {_prefix(str(key))}."
                )
            if key in properties:
                _validate_schema(value, properties[key], _prefix(key))
        return

    if expected_type == "array":
        if not isinstance(data, list):
            raise LLMOutputSchemaError(f"{path or 'value'} must be an array.")
        items_schema = schema.get("items")
        if items_schema is None:
            return
        for idx, item in enumerate(data):
            _validate_schema(item, items_schema, f"{path}[{idx}]")
        return

    if expected_type == "string":
        if not isinstance(data, str):
            raise LLMOutputSchemaError(f"{path or 'value'} must be a string.")
        return

    if expected_type == "number":
        if isinstance(data, bool) or not isinstance(data, (int, float)):
            raise LLMOutputSchemaError(f"{path or 'value'} must be a number.")
        if isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
            raise LLMOutputSchemaError(f"{path or 'value'} must be a finite number.")
        return

    if expected_type == "integer":
        if isinstance(data, bool) or not isinstance(data, int):
            raise LLMOutputSchemaError(f"{path or 'value'} must be an integer.")
        return

    if expected_type == "boolean":
        if not isinstance(data, bool):
            raise LLMOutputSchemaError(f"{path or 'value'} must be a boolean.")
        return

    if expected_type == "null":
        if data is not None:
            raise LLMOutputSchemaError(f"{path or 'value'} must be null.")
        return



def _normalize_structured_output(data: Any, schema: Mapping[str, Any]) -> Any:
    if schema is CHECKER_OUTPUT_SCHEMA and isinstance(data, list):
        return {"errors": data}
    return data


class BaseLLM(ABC):
    """Small abstraction for local and API backed LLM clients."""

    backend_name: str
    timeout_seconds: float | None = None
    temperature: float | None = None
    max_new_tokens: int | None = None

    def __init__(
        self,
        timeout_seconds: float | None = None,
        temperature: float | None = None,
        max_new_tokens: int | None = None,
    ) -> None:
        if timeout_seconds is not None:
            self.timeout_seconds = float(timeout_seconds)
        if temperature is not None:
            self.temperature = float(temperature)
        if max_new_tokens is not None:
            self.max_new_tokens = int(max_new_tokens)

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> str:
        raise NotImplementedError

    def _build_retry_prompt(self, base_prompt: str, error: Exception, last_raw: str | None = None) -> str:
        suffix = f"Previous response:\n{last_raw}" if last_raw else "No response was returned."
        return (
            f"{base_prompt}\\n\\n"
            "Your previous response was not valid JSON for the required schema. "
            "Please return strict JSON only, with no markdown, prose, or extra text.\\n"
            f"Error: {error}\\n"
            f"{suffix}"
        )

    def complete_json(
        self,
        prompt: str,
        schema: Mapping[str, Any] | None,
        *,
        max_retries: int = 3,
        timeout_seconds: float | None = None,
        retry_delay_seconds: float = 1.0,
        **kwargs: Any,
    ) -> Any:
        if schema is None:
            timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds
            return self.generate(prompt, timeout_seconds=timeout, **kwargs)

        working_prompt = (
            f"{prompt}\\n\\n"
            "Return only strict JSON matching this schema and nothing else.\\n"
            f"{json.dumps(schema, ensure_ascii=False)}"
        )
        base_prompt = working_prompt
        timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds
        last_raw: str | None = None
        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            if attempt > 1 and last_raw is not None and last_error is not None:
                working_prompt = self._build_retry_prompt(base_prompt, last_error, last_raw)
                time.sleep(retry_delay_seconds * (attempt - 1))

            raw_output = self.generate(working_prompt, timeout_seconds=timeout, **kwargs)
            last_raw = raw_output
            try:
                parsed = parse_json_output(raw_output)
            except LLMOutputParseError as exc:
                last_error = exc
                if attempt >= max_retries:
                    raise
                continue
            parsed = _normalize_structured_output(parsed, schema)
            try:
                _validate_schema(parsed, schema)
            except LLMOutputSchemaError as exc:
                last_error = exc
                if attempt >= max_retries:
                    raise
                continue
            return parsed

        if last_error is not None:
            raise last_error
        raise LLMOutputError("Could not obtain a valid structured model response.")

    def complete_reviser_output(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return self.complete_json(prompt, REVISER_OUTPUT_SCHEMA, **kwargs)

    def complete_checker_output(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return self.complete_json(prompt, CHECKER_OUTPUT_SCHEMA, **kwargs)
