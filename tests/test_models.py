from types import SimpleNamespace

from item_reviser.models.base import BaseLLM, REVISER_OUTPUT_SCHEMA
from item_reviser.models.hf_local import HuggingFaceLocalModel


class BadThenGoodLLM(BaseLLM):
    backend_name = "bad_then_good"

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs,
    ) -> str:
        _ = prompt, timeout_seconds, kwargs
        self.calls += 1
        if self.calls == 1:
            return "not json"
        return (
            '{"question":"Q?","response_options":[],"revision_notes":[],"changed":false}'
        )


class RecordingPipeline:
    def __init__(self) -> None:
        self.kwargs = {}

    def __call__(self, prompt: str, **kwargs):
        self.kwargs = kwargs
        return [{"generated_text": f"{prompt}answer"}]


def test_complete_json_retries_with_repair_prompt():
    model = BadThenGoodLLM()

    result = model.complete_json(
        "Return a revision.",
        REVISER_OUTPUT_SCHEMA,
        max_retries=2,
        retry_delay_seconds=0,
    )

    assert result["question"] == "Q?"
    assert model.calls == 2


def test_hf_sampling_decoding_configures_generation_kwargs():
    pipeline = RecordingPipeline()
    model = HuggingFaceLocalModel(
        model_path="/tmp/model",
        decoding_method="sampling",
        temperature=0.8,
        top_p=0.9,
        top_k=40,
        max_new_tokens=32,
    )
    model._pipeline = pipeline
    model._tokenizer = SimpleNamespace(eos_token_id=2)

    output = model.generate("prompt:")

    assert output == "answer"
    assert pipeline.kwargs["do_sample"] is True
    assert pipeline.kwargs["temperature"] == 0.8
    assert pipeline.kwargs["top_p"] == 0.9
    assert pipeline.kwargs["top_k"] == 40
    assert pipeline.kwargs["max_new_tokens"] == 32


def test_hf_beam_search_configures_generation_kwargs():
    pipeline = RecordingPipeline()
    model = HuggingFaceLocalModel(
        model_path="/tmp/model",
        decoding_method="beam_search",
        num_beams=4,
    )
    model._pipeline = pipeline
    model._tokenizer = SimpleNamespace(eos_token_id=2)

    model.generate("prompt:")

    assert pipeline.kwargs["do_sample"] is False
    assert pipeline.kwargs["num_beams"] == 4
