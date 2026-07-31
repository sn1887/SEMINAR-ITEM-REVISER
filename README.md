# Seminar Item Reviser

Advanced research repository for a **Survey Questionnaire Item Reviser Agent**.

This repository is designed for the LMU seminar *LLM Agents for Survey Questionnaire Design*. It focuses on the later part of the seminar pipeline: **item quality checking** and **item revision**. The code is deliberately modular so that the same evaluation set can later be used to benchmark different local LRZ models such as Qwen, Llama, DeepSeek, Gemma, or any OpenAI-compatible local server.

The repository follows a research-lab style setup:

- Hydra configuration for every experiment.
- Immutable experiment outputs saved under `outputs/` by Hydra.
- Model backends are swappable through config, not hard-coded paths.
- Agent prompts are selected through config and stored as editable Markdown templates.
- A 1,000-item gold evaluation set is included under `data/eval/final_gold_1000.jsonl`.
- The older 200-item synthetic seed set remains available under `data/eval/test_set_200_seed.jsonl`.
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
      "severity": "high",
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

Severity uses an impact scale: `low` means minor risk and the item is mostly
answerable; `medium` means the issue likely affects interpretation or response
quality; `high` means the issue likely invalidates measurement or makes responses
misleading.

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

Evaluate the default 1,000-item gold set:

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

In `report.md`, metric prominence depends on `evaluator.mode`. End-to-end and
detection-only runs foreground detector metrics such as precision, recall, F1,
exact label-set match, and clean false-positive rate. Oracle-revision runs mark
detection metrics as oracle-supplied and foreground semantic revision metrics
instead. `metrics.json` records this under `metric_applicability`.

For faster development runs, override the data config to use the older seed set:

```bash
python scripts/evaluate.py \
  data=eval_200 \
  experiment.max_items=20
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
    template_path: ${paths.prompt_dir}/agents/baseline/quality_checker.md
    max_retries: 3
    timeout_seconds: 120
  item_reviser:
    template_path: ${paths.prompt_dir}/agents/baseline/item_reviser.md
    max_retries: 3
    timeout_seconds: 120
```

This makes prompt versions easy to compare:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/path/to/model \
  prompt.quality_checker.template_path=prompts/agents/baseline/quality_checker.md
```

Prompt templates use simple `$placeholder` substitution for fields such as
`${question}`, `${response_options}`, `${allowed_categories}`, and
`${detected_issues}`.

The final matrix keeps `baseline_codebook` and `orchestration_codebook` as P0
controls. P1 (`baseline_p1`, `orchestration_p1`) is additive: it preserves the
P0 codebook, taxonomy boundaries, clean-item rules, severity guidance, routing
behavior, and revision safeguards, then adds operational response-option rules.
P2 (`baseline_p2`, `orchestration_p2`) preserves P1 and adds 28 independently
authored, role-specific calibration examples across the two runtime paths. All six
P0/P1/P2 prompt packs are opt-in Hydra choices. P2 examples are automatically checked
for exact and near overlap with v4 questions and gold revisions.

---

## 6. Optional LLM orchestration

The default behavior remains the original single-pass LLM quality-checker plus
LLM reviser. The full router, planner, specialist, fallback, validator, and
bounded-retry workflow is opt-in:

```bash
python scripts/run_item_reviser.py orchestration.enabled=true
```

For evaluation:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/path/to/model \
  orchestration.enabled=true
```

Orchestration behavior is configured in `configs/orchestration/default.yaml`.
Agent prompt slots live in `configs/prompt/default.yaml` and point to Markdown
templates under `prompts/agents/orchestration/`, including `router`,
`revision_planner`, `fallback_reviser`, the five specialist families, and
`validator`. The non-orchestrated quality checker and item reviser prompts live
under `prompts/agents/baseline/`.

Use the minimal zero-shot baseline:

```bash
python scripts/evaluate.py \
  data=final_gold_200_v3_pure_loaded \
  prompt=default \
  orchestration.enabled=false \
  evaluator.mode=end_to_end
```

Use the zero-shot codebook prompt:

```bash
python scripts/evaluate.py \
  data=final_gold_200_v3_pure_loaded \
  prompt=baseline_codebook \
  orchestration.enabled=false \
  evaluator.mode=end_to_end
```

Use the orchestrated codebook router/fallback prompts:

```bash
python scripts/evaluate.py \
  data=final_gold_200_v3_pure_loaded \
  prompt=orchestration_codebook \
  orchestration.enabled=true \
  evaluator.mode=end_to_end
```

The baseline non-orchestrated pipeline also has runtime knobs in
`configs/agent/item_reviser.yaml`, including:

- `use_llm_for_quality_checking`
- `use_llm_for_revision`
- `skip_revision_when_no_errors`
- `unchanged_revision_notes`

The orchestration config now exposes not just `enabled`, but also nested routing
and validation policies, for example:

```yaml
orchestration:
  enabled: true
  confidence_threshold: 0.75
  retry_budget: 1
  strategy: single_specialist
  multi_label_strategy: fallback
  routing:
    low_confidence_action: fallback
    multi_label_action: fallback
  validation:
    enabled: true
    validate_accept_path: true
    accept_failure_action: fallback
```

When enabled, prediction rows include an `orchestration_trace` plus flattened
evaluation fields for route, router decision, taxonomy labels, confidence,
selected agent, retry count, validation status, and final status. See
`docs/orchestration_usage.md` for the full config and prompt customization guide.

---

## 7. Evaluation modes

`evaluator.mode` separates detection from revision:

- `end_to_end`: current default; detect issues and revise from predicted issues.
- `detection_only`: run only the checker or orchestration router and leave the
  item unchanged. Semantic revision metrics and overcorrection are not applicable.
- `oracle_revision`: skip detection, use dataset gold labels as detected issues,
  and evaluate revision quality independent of detection. Detection metrics are
  oracle-supplied audit values, not model-detection performance.

Examples:

```bash
python scripts/evaluate.py data=final_gold_200_v3_pure_loaded evaluator.mode=detection_only
python scripts/evaluate.py data=final_gold_200_v3_pure_loaded evaluator.mode=oracle_revision
python scripts/evaluate.py data=final_gold_200_v3_pure_loaded evaluator.mode=end_to_end
```

---

## 8. MLflow progress logging

When `tracking.enabled=true`, evaluation now opens the MLflow run before the item
loop and logs partial metrics as the run progresses. The default interval is
every 5 completed items:

```yaml
tracking:
  log_progress_every_items: 5
```

Override this for longer or shorter runs:

```bash
python scripts/evaluate.py tracking.log_progress_every_items=10
```

Set `tracking.log_progress_every_items=0` to return to final-only metric logging.

Semantic question-revision metrics are final-only: one cached CPU BERTScore
scorer produces question BERTScore F1, while Evaluate's SARI scores source ->
generated question against the gold revision. Response options have no semantic
similarity metric because the available custom heuristic was not sufficiently
validated for final reporting. Exact option match remains as a strict diagnostic
that can under-credit valid alternatives. The metrics apply only to flawed rows
with valid expected questions; they log coverage, failures, the BERTScore hash,
Torch/Transformers/metric-library versions, and configuration to MLflow. See
[the evaluation plan](docs/evaluation_plan.md) and
[the final matrix](docs/final_26_experiment_matrix.md) for scales, limitations,
and the 26-run schedule.

---

## 9. Failure-resilient evaluation

Long model benchmarks continue when a single item produces malformed JSON, a
schema mismatch, or another item-level model error. The failed item is written to
`predictions.jsonl` with an `error` block, left unchanged, and counted in
`failed_items` and `failure_rate`.

```yaml
evaluator:
  continue_on_item_error: true
  write_predictions_incrementally: true
  include_error_traceback: true
```

Set `evaluator.continue_on_item_error=false` when debugging and you want the run
to stop at the first invalid model response.
