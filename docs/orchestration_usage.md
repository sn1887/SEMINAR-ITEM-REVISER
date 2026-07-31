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
  data=final_gold_200_v4 \
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

Known treatment packs must match the active pipeline:

| Pack | Required runtime path |
| --- | --- |
| `baseline_codebook`, `baseline_p1`, `baseline_p2` | `orchestration.enabled=false` |
| `orchestration_codebook`, `orchestration_p1`, `orchestration_p2` | `orchestration.enabled=true` |

The pipeline rejects cross-family pairings before creating agents. Unnamed,
custom, and `default` prompt configs remain available for development uses that
intentionally supply both sets of slots.

P1 adds operational response-option and format rules. P2 adds a fixed, targeted
set of option/format calibration examples; it is not unrestricted few-shot
prompting for every taxonomy category. See `prompts/agents/README.md` for the
per-role example counts, demonstrated boundaries, and categories without a
direct example.

P0 remains zero-shot and example-free. Its loaded/completeness boundary no
longer suppresses unrelated independent labels, its orchestration router drops
unreachable severity-calibration guidance because severity is not in the router
schema, and its shared validator makes `fixes_detected_issue` nullable/not
applicable on a clean accept path. Taxonomy and revision rules otherwise remain
unchanged.

Common placeholders include:

- `${allowed_categories}`
- `${question}`
- `${response_options}`
- `${output_schema}`
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

`open_closed_mismatch` maps to `questionnaire_format`. The P1 and P2
orchestration packs select their matching P1/P2 format-specialist prompt; the
response-options specialist is not responsible for this format category.

Router confidence describes certainty in the route or label decision. The
router schema has no severity field and the router does not predict severity.
The `medium` value attached to routed `CheckResult` objects is synthetic
compatibility metadata only; it must never be compared with or reported as
model-predicted baseline severity.

The validator can return:

- `pass`: final output is accepted.
- `retry`: retry through the revision path while retry budget remains.
- `manual_review`: final output is flagged for manual review.
- `failed`: reserved for a candidate that cannot be evaluated from the supplied
  information; it is treated as manual review unless a retry is available.

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
