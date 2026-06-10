# LLM Orchestration Usage

`docs/orchestration_diagram.md` is the source of truth for the target workflow.
The generated image is illustrative only.

The repository still uses the original single-pass LLM quality-checker plus LLM
reviser by default. Orchestration is opt-in:

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

## Config Surface

The default config lives in `configs/orchestration/default.yaml`.

Important fields:

- `enabled`: keeps orchestration disabled unless explicitly set to `true`.
- `strategy`: `single_specialist` by default; `sequential_specialists` enables
  simple ordered handling for multi-label cases.
- `multi_label_strategy`: `fallback` by default; set to `sequential` together
  with `strategy=sequential_specialists` for sequential specialists.
- `confidence_threshold`: router confidence below this value goes to fallback.
- `retry_budget`: validator-requested orchestration retries, separate from JSON
  repair retries in prompt configs.
- `taxonomy_labels`: the supported issue labels.
- `specialist_families`: maps taxonomy labels to specialist families.
- `agent_prompt_names`: maps orchestration roles to prompt config keys.

Example:

```yaml
orchestration:
  enabled: true
  confidence_threshold: 0.75
  retry_budget: 1
  strategy: single_specialist
  multi_label_strategy: fallback
```

## Prompt Customization

Prompt slots are configured in `configs/prompt/default.yaml` and point to
Markdown templates in `prompts/agents/`:

- `router`
- `revision_planner`
- `fallback_reviser`
- `wording_clarity`
- `response_options_scale`
- `construct_alignment`
- `bias_sensitivity`
- `questionnaire_format`
- `validator`

Each prompt receives an injected JSON schema through `${output_schema}` and must
return strict JSON only. The Python agents do not hardcode prompt text.

Common placeholders include:

- `${allowed_categories}`
- `${item_id}`
- `${question}`
- `${response_options}`
- `${target_concept}`
- `${topic}`
- `${router_decision}`
- `${detected_issues}`
- `${revision_plan}`
- `${candidate_revision}`
- `${retry_instructions}`
- `${trace_context}`

## Routing Behavior

The router can return `accept`, `revise`, or `fallback`.

Fallback is selected for low confidence, unknown labels, mixed labels by default,
unsupported families, contradictory router output, and explicit fallback
recommendations. A single supported label routes through the planner to the
configured specialist family.

The validator can return:

- `pass`: final output is accepted.
- `retry`: retry through the revision path while retry budget remains.
- `manual_review`: final output is flagged for manual review.
- `failed`: treated as manual review unless a retry is available.

## Trace Output

When orchestration is enabled, prediction rows include:

- `orchestration_trace`: full compact trace with attempts.
- `orchestration`: flattened evaluation fields:
  - `orchestration_enabled`
  - `route`
  - `router_decision`
  - `taxonomy_labels`
  - `confidence`
  - `selected_agent`
  - `retry_count`
  - `validation_status`
  - `final_status`

Evaluation metrics also include an `orchestration` summary with route, decision,
agent, validation, final-status, and retry-count aggregates.
