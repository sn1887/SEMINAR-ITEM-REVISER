import json
from types import SimpleNamespace

from omegaconf import OmegaConf

from item_reviser.agents.orchestration import REVISION_PLAN_OUTPUT_SCHEMA
from item_reviser.models.base import BaseLLM, REVISER_OUTPUT_SCHEMA
from item_reviser.models.factory import build_model
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


class FakeTensor:
    shape = (1, 3)

    def to(self, device: str):
        _ = device
        return self


class FakeGeneratedIds:
    def __getitem__(self, key):
        _ = key
        return self


class RecordingModel:
    def __init__(self) -> None:
        self.kwargs = {}

    def parameters(self):
        yield SimpleNamespace(device="cpu")

    def generate(self, **kwargs):
        self.kwargs = kwargs
        return FakeGeneratedIds()


class FakeTokenizer:
    eos_token_id = 2

    def __call__(self, prompt: str, return_tensors: str):
        _ = prompt, return_tensors
        return {"input_ids": FakeTensor()}

    def batch_decode(
        self,
        generated_ids,
        *,
        skip_special_tokens: bool,
        clean_up_tokenization_spaces: bool,
    ):
        _ = generated_ids, skip_special_tokens, clean_up_tokenization_spaces
        return ["answer"]


class TestableHuggingFaceLocalModel(HuggingFaceLocalModel):
    def _load_pipeline(self) -> None:
        return None


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


class NullFieldLLM(BaseLLM):
    backend_name = "null_field"

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs,
    ) -> str:
        _ = prompt, timeout_seconds, kwargs
        return (
            '{"repair_family":"fallback","selected_agent":"fallback_reviser",'
            '"instructions":[],"fallback_reason":null,"rationale":"Use fallback."}'
        )


def test_complete_json_accepts_nullable_optional_string_fields():
    model = NullFieldLLM()

    result = model.complete_json(
        "Return a revision plan.",
        REVISION_PLAN_OUTPUT_SCHEMA,
        max_retries=1,
        retry_delay_seconds=0,
    )

    assert result["repair_family"] == "fallback"
    assert result["fallback_reason"] is None


def test_hf_sampling_decoding_configures_generation_kwargs():
    recording_model = RecordingModel()
    model = TestableHuggingFaceLocalModel(
        model_path="/tmp/model",
        decoding_method="sampling",
        temperature=0.8,
        top_p=0.9,
        top_k=40,
        max_new_tokens=32,
    )
    model._model = recording_model
    model._tokenizer = FakeTokenizer()

    output = model.generate("prompt:")

    assert output == "answer"
    assert recording_model.kwargs["do_sample"] is True
    assert recording_model.kwargs["temperature"] == 0.8
    assert recording_model.kwargs["top_p"] == 0.9
    assert recording_model.kwargs["top_k"] == 40
    assert recording_model.kwargs["max_new_tokens"] == 32


def test_hf_beam_search_configures_generation_kwargs():
    recording_model = RecordingModel()
    model = TestableHuggingFaceLocalModel(
        model_path="/tmp/model",
        decoding_method="beam_search",
        num_beams=4,
    )
    model._model = recording_model
    model._tokenizer = FakeTokenizer()

    model.generate("prompt:")

    assert recording_model.kwargs["do_sample"] is False
    assert recording_model.kwargs["num_beams"] == 4


def test_hf_thinking_config_resets_to_false_when_template_does_not_support_it(
    tmp_path,
):
    model_dir = tmp_path / "plain-model"
    model_dir.mkdir()
    (model_dir / "tokenizer_config.json").write_text(
        json.dumps({"chat_template": "{{ messages }}"}),
        encoding="utf-8",
    )
    cfg = OmegaConf.create(
        {
            "backend": "hf_local",
            "model_path": str(model_dir),
            "chat_template": {"enable_thinking": True},
        }
    )

    model = build_model(cfg)

    assert isinstance(model, HuggingFaceLocalModel)
    assert model.requested_enable_thinking is True
    assert model.supports_enable_thinking is False
    assert model.enable_thinking is False
    assert cfg.chat_template.enable_thinking is False
    assert cfg.chat_template.supports_enable_thinking is False


def test_hf_thinking_config_stays_true_when_template_supports_it(tmp_path):
    model_dir = tmp_path / "thinking-model"
    model_dir.mkdir()
    (model_dir / "tokenizer_config.json").write_text(
        json.dumps(
            {
                "chat_template": (
                    "{% if enable_thinking is defined and enable_thinking %}"
                    "<think>{% endif %}"
                )
            }
        ),
        encoding="utf-8",
    )
    cfg = OmegaConf.create(
        {
            "backend": "hf_local",
            "model_path": str(model_dir),
            "chat_template": {"enable_thinking": True},
        }
    )

    model = build_model(cfg)

    assert isinstance(model, HuggingFaceLocalModel)
    assert model.requested_enable_thinking is True
    assert model.supports_enable_thinking is True
    assert model.enable_thinking is True
    assert cfg.chat_template.enable_thinking is True
    assert cfg.chat_template.supports_enable_thinking is True
