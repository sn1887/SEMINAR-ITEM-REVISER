# Agent Prompt Layout

Prompt bodies are separated by treatment and runtime path:

- `baseline/`: prompts used by the default non-orchestrated pipeline when
  `orchestration.enabled=false`.
- `baseline_codebook/`: the P0 zero-shot codebook control for the baseline
  checker and reviser.
- `orchestration/`: prompts used by the opt-in router, planner, specialist,
  fallback, and validator workflow. These files also supply the P0 roles reused
  by later orchestration treatments.
- `orchestration_codebook/`: the P0 zero-shot codebook router and fallback
  control; its other orchestration roles come from `orchestration/`.
- `baseline_p1/`: P0 baseline content plus operational response-option rules.
- `orchestration_p1/`: P1 router, fallback, response-options specialist,
  questionnaire-format specialist, and validator. The planner and wording,
  construct, and bias specialists reuse P0 files from `orchestration/`.
- `baseline_p2/` and `orchestration_p2/`: P1 plus fixed, independently authored
  role-appropriate calibration examples. P2 is targeted response-option and
  open/closed-format calibration, not unrestricted few-shot prompting across all
  taxonomy labels.

P0 remains zero-shot and receives no calibration example. Three narrow
consistency repairs affect its shared rules: the loaded/completeness boundary no
longer suppresses unrelated independent labels; the orchestration router no
longer discusses severity because its schema has no severity field; and the
validator uses nullable/not-applicable `fixes_detected_issue` on a clean accept
path. The taxonomy and revision rules otherwise remain unchanged.

## P2 Demonstration Scope

| Runtime role | Examples | Demonstrated boundary or behavior |
| --- | ---: | --- |
| Baseline quality checker | 3 | Overlap versus completeness; agreement proxy versus an item-specific construct; clean-item acceptance |
| Baseline item reviser | 3 | Minimal overlap repair; direct item-specific scale repair; unchanged clean item |
| Orchestration router | 4 | `non_exclusive_options` routing; `agree_disagree_scale` routing; `open_closed_mismatch` routing; clean `accept` |
| Fallback reviser | 3 | Same-family `incomplete_options` + `non_exclusive_options`; conservative low-confidence `missing_scale_labels`; preservation when an `incomplete_options` repair would be speculative |
| Response-options specialist | 3 | Minimal `non_exclusive_options` repair; `agree_disagree_scale` repair; rejection of a speculative `incomplete_options` addition |
| Questionnaire-format specialist | 2 | Open narrative paired with fixed ratings; exact-entry request paired with grouped closed categories |
| Validator | 3 | Clean accept-path `pass`; focused `retry` for an unfixed overlap; `manual_review` for construct drift |
| Planner, wording, construct, and bias roles | 0 | No P2 demonstration; unchanged P0 prompts |

The option categories with no direct P2 demonstration are `unbalanced_scale`,
`too_many_scale_points`, and `polarity_mismatch`. P1 still gives operational
rules for them. Any P2 improvement on those categories, or on wording,
construct, and bias categories, must be interpreted as rule use or
generalization rather than a direct in-context-example effect.

## Runtime Selection

The active prompt slots and file paths are configured in
`configs/prompt/*.yaml`. Known treatment packs are pipeline-specific and fail
fast when paired incorrectly:

| Treatment | Baseline pipeline (`orchestration.enabled=false`) | Orchestrated pipeline (`orchestration.enabled=true`) |
| --- | --- | --- |
| P0 | `prompt=baseline_codebook` | `prompt=orchestration_codebook` |
| P1 | `prompt=baseline_p1` | `prompt=orchestration_p1` |
| P2 | `prompt=baseline_p2` | `prompt=orchestration_p2` |

Unnamed, custom, and `prompt=default` configurations remain usable on either
path. The P1/P2 orchestration configs wire `questionnaire_format` to their
matching P1/P2 specialist file, so `open_closed_mismatch` does not fall back to
the P0 format prompt.
