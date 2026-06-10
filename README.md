# Seminar Item Reviser

Advanced research repository for a **Survey Questionnaire Item Reviser Agent**.

This repository is designed for the LMU seminar *LLM Agents for Survey Questionnaire Design*. It focuses on the later part of the seminar pipeline: **item quality checking** and **item revision**. The code is deliberately modular so that the same evaluation set can later be used to benchmark different local LRZ models such as Qwen, Llama, DeepSeek, Gemma, or any OpenAI-compatible local server.

The repository follows a research-lab style setup:

- Hydra configuration for every experiment.
- Immutable experiment outputs saved under `outputs/` by Hydra.
- Model backends are swappable through config, not hard-coded paths.
- Agent prompts are selected through config and stored as editable Markdown templates.
- A 200-item synthetic seed evaluation set is included under `data/eval/test_set_200_seed.jsonl`.
- Evaluation produces machine-readable predictions, metrics, and a human-readable report.
- Seminar progress documentation is integrated under `docs/` and `reports/`.

---

## 1. What this project does

Given a survey item such as:

```text
Don’t you agree that stricter environmental regulations are necessary?
```

The agent should return:

```json
{
  "errors": [
    {
      "category": "leading_question",
      "explanation": "The wording suggests that agreement is the expected answer."
    }
  ],
  "revised_item": {
    "question": "To what extent do you support or oppose stricter environmental regulations?",
    "response_options": [
      "Strongly oppose", "Somewhat oppose", "Neither support nor oppose", "Somewhat support", "Strongly support"
    ]
  }
}
```

The current implementation is an **LLM-agent evaluation scaffold**:

1. configurable LLM model interface,
2. configurable prompt registry,
3. quality-checking agent,
4. item-revision agent,
5. evaluation pipeline.

The design is set up for benchmarking local LRZ models and OpenAI-compatible local servers.

---

## 2. Repository map

```text
seminar-item-reviser/
├── configs/                 # Hydra experiment, model, data, agent, evaluator configs
├── data/                    # Seed evaluation data and examples
├── docs/                    # Research design, evaluation plan, protocol, LRZ notes
├── prompts/                 # Prompt templates and rubric files
├── reports/                 # Progress-report templates and generated reports
├── scripts/                 # Hydra/CLI entrypoints
├── slurm/                   # LRZ/SLURM job templates
├── src/item_reviser/        # Main Python package
├── tests/                   # Unit tests and smoke-test fixtures
├── Makefile                 # Common commands
├── pyproject.toml           # Package metadata and tooling
└── README.md
```

See `docs/repository_design.md` for a detailed explanation.

---

## 3. Quick start locally

Create an environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Run the local control-flow smoke test:

```bash
python scripts/smoke_test.py
```

Evaluate the included 200-item seed set:

```bash
python scripts/evaluate.py \
  experiment=item_reviser_eval \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL
```

Hydra will create an experiment directory such as:

```text
outputs/2026-06-06/12-00-00/
├── .hydra/
│   ├── config.yaml
│   ├── hydra.yaml
│   └── overrides.yaml
├── predictions.jsonl
├── metrics.json
└── report.md
```

---

## 4. Flexible local model setup

For a local Hugging Face model path:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL \
  model.decoding.method=greedy
```

Supported local-HF decoding methods are `greedy`, `sampling`, `beam_search`, and `beam_sample`. For example:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL \
  model.decoding.method=sampling \
  model.decoding.temperature=0.7 \
  model.decoding.top_p=0.9
```

For a local vLLM/OpenAI-compatible server:

```bash
python scripts/evaluate.py \
  model=openai_compatible \
  model.base_url=http://localhost:8000/v1 \
  model.model_name=YOUR_MODEL_NAME
```

The repository does **not** assume one fixed model because the seminar may benchmark multiple local models later.

---

## 5. Prompt configuration

Prompt bodies live in Markdown files under `prompts/`, while Hydra chooses which
template each agent uses:

```yaml
prompt:
  quality_checker:
    template_path: ${paths.prompt_dir}/agents/quality_checker.md
    max_retries: 3
    timeout_seconds: 120
  item_reviser:
    template_path: ${paths.prompt_dir}/agents/item_reviser.md
    max_retries: 3
    timeout_seconds: 120
```

This makes prompt versions easy to compare:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/path/to/model \
  prompt.quality_checker.template_path=prompts/agents/quality_checker.md
```

Prompt templates use simple `$placeholder` substitution for fields such as
`${question}`, `${response_options}`, `${allowed_categories}`, and
`${detected_issues}`.
