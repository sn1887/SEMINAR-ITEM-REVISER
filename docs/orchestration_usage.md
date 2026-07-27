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

For the codebook-hardened orchestration prompt variant:

```bash
python scripts/evaluate.py \
  data=final_gold_200_v3_pure_loaded \
  prompt=orchestration_codebook \
  orchestration.enabled=true \
  evaluator.mode=end_to_end
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
- `routing.*`: policy switches for low confidence, unknown labels, router
  fallback decisions, contradictory accept outputs, missing taxonomy labels,
  unsupported families, multi-label fallback, and mixed-family fallback.
- `validation.enabled`: toggles validator calls for revision candidates.
- `validation.validate_accept_path`: controls whether accepted items are also
  passed through the validator.
- `validation.accept_failure_action`: chooses whether a rejected accept-path
  item goes to `fallback` or direct `manual_review`.

Example:

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

The baseline non-orchestrated pipeline also has Hydra runtime controls in
`configs/agent/item_reviser.yaml`:

- `use_llm_for_quality_checking`
- `use_llm_for_revision`
- `skip_revision_when_no_errors`
- `unchanged_revision_notes`

## Prompt Customization

Prompt slots are configured in `configs/prompt/default.yaml` and point to
Markdown templates in `prompts/agents/orchestration/`:

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

The non-orchestrated baseline prompts are kept separately in
`prompts/agents/baseline/`:

- `quality_checker`
- `item_reviser`

The zero-shot codebook baseline prompts live in
`prompts/agents/baseline_codebook/` and are selected with
`prompt=baseline_codebook`. The orchestration codebook router/fallback prompts
live in `prompts/agents/orchestration_codebook/` and are selected with
`prompt=orchestration_codebook`.

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

Fallback is still the default for low confidence, unknown labels, mixed labels,
unsupported families, contradictory router output, and explicit fallback
recommendations, but those route choices can now be changed from config without
touching Python. A single supported label routes through the planner to the
configured specialist family.

Severity and confidence are separate concepts. Severity describes the
measurement harm of a detected issue: `low` is minor risk and the item is mostly
answerable; `medium` likely affects interpretation or response quality; `high`
likely invalidates measurement or makes responses misleading. Router confidence
describes certainty in the route or label decision.

The validator can return:

- `pass`: final output is accepted.
- `retry`: retry through the revision path while retry budget remains.
- `manual_review`: final output is flagged for manual review.
- `failed`: treated as manual review unless a retry is available.

When validation is disabled through config, traces record
`validation_status=skipped`.

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
