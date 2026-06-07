# Seminar Item Reviser

Advanced research repository for a **Survey Questionnaire Item Reviser Agent**.

This repository is designed for the LMU seminar *LLM Agents for Survey Questionnaire Design*. It focuses on the later part of the seminar pipeline: **item quality checking** and **item revision**. The code is deliberately modular so that the same evaluation set can later be used to benchmark different local LRZ models such as Qwen, Llama, DeepSeek, Gemma, or any OpenAI-compatible local server.

The repository follows a research-lab style setup:

- Hydra configuration for every experiment.
- Immutable experiment outputs saved under `outputs/` by Hydra.
- Model backends are swappable through config, not hard-coded paths.
- A deterministic `mock` backend is included for smoke tests and CI.
- A 200-item synthetic seed evaluation set is included under `data/eval/test_set_200_seed.jsonl`.
- Evaluation produces machine-readable predictions, metrics, and a human-readable report.
- Seminar progress documentation is integrated under `docs/` and `reports/`.

> Note: "DeepMind style" here means a reproducible, configuration-first, modular research repository pattern. It is not an official DeepMind template.

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

The current implementation is a **hybrid baseline**:

1. deterministic rule-based quality checks,
2. configurable LLM model interface,
3. item revision component,
4. evaluation pipeline.

The design is intentionally ready for replacing the mock model with local models on LRZ.

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

Run a smoke test with the deterministic mock backend:

```bash
python scripts/run_item_reviser.py \
  item.question="Don’t you agree that stricter environmental regulations are necessary?" \
  item.response_options='["Strongly disagree", "Disagree", "Agree", "Strongly agree"]'
```

Evaluate the included 200-item seed set:

```bash
python scripts/evaluate.py experiment=item_reviser_eval model=mock
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

The baseline uses:

```bash
python scripts/evaluate.py model=mock
```

For a local Hugging Face model path:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/YOUR_MODEL
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

## 5. Evaluation target for next week

For the next meeting, the key progress target is:

- show that the repo runs end-to-end,
- explain the 200-item evaluation/test set design,
- report baseline metrics with `model=mock`,
- list open questions for Bolei and Caro.

Use:

```bash
python scripts/evaluate.py experiment=item_reviser_eval model=mock
```

Then summarize the generated `report.md` in `reports/progress_next_week_template.md`.

---

## 6. Important caveat about the included 200-item set

`data/eval/test_set_200_seed.jsonl` is a **seed evaluation set**, not a final gold standard. It is useful for pipeline development and initial reporting, but it should be manually audited before being treated as the final seminar evaluation set.

Recommended next step: review 20–30 items with Caro/Bolei, agree on taxonomy boundaries, then finalize the 200 items.
