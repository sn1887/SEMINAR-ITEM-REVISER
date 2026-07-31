# Agent Prompt Layout

This directory contains separate prompt packs for two runtime roles and three
additive experimental conditions.

## Runtime paths

- `baseline/`: default non-orchestrated checker and reviser prompts.
- `baseline_codebook/`: baseline P0 zero-shot taxonomy-codebook control.
- `baseline_p1/`: baseline P0 behavior plus operational response-option and
  questionnaire-format procedures.
- `baseline_p2/`: baseline P1 behavior plus fixed targeted calibration examples.
- `orchestration/`: shared router/planner/specialist/fallback/validator role prompts.
  The planner and wording, construct, and bias specialists are reused across P0–P2.
- `orchestration_codebook/`: orchestrated P0 router and fallback control.
- `orchestration_p1/`: P0 orchestration behavior plus operational option/format rules.
- `orchestration_p2/`: P1 orchestration behavior plus fixed targeted examples.

Keep baseline and orchestrated prompt packs separate. Baseline prompts perform a
checker-then-reviser workflow; orchestration prompts divide responsibility among the
router, planner, specialists, fallback reviser, and validator.

## Additive experimental design

- **P0 — zero-shot taxonomy codebook control.** Uses all 16 canonical definitions,
  explicit boundaries, an evidence gate, independent-label logic, and clean-item
  preservation without demonstrations.
- **P1 — operational response-option and format rules.** Retains P0 verbatim and adds
  ordered procedures for response mode, item-specific dimension/unit, agreement
  proxies, completeness, exclusivity, balance, labels, granularity, polarity, and
  open/closed compatibility.
- **P2 — targeted role-specific few-shot calibration.** Retains P1 verbatim and adds
  schema-valid examples only for selected response-option, scale, format, clean-path,
  routing, fallback, and validation decisions. It is not representative few-shot
  coverage of all 16 taxonomy labels.

The build validation report checks literal P0→P1→P2 containment after the final JSON
instruction is normalized.

## Canonical runtime identifiers

Taxonomy labels:
`leading_question`, `loaded_question`, `double_barreled`, `recall_error`,
`vague_ambiguous`, `sensitive_topic_direct`, `social_desirability`,
`negative_wording`, `open_closed_mismatch`, `agree_disagree_scale`,
`unbalanced_scale`, `incomplete_options`, `non_exclusive_options`,
`missing_scale_labels`, `too_many_scale_points`, and `polarity_mismatch`.

Router decisions: `accept`, `revise`, `fallback`.

Repair families: `wording_clarity`, `response_options_scale`,
`construct_alignment`, `bias_sensitivity`, `questionnaire_format`, `fallback`.

Agent identifiers: `router`, `revision_planner`, `fallback_reviser`, `validator`,
`wording_clarity`, `response_options_scale`, `construct_alignment`,
`bias_sensitivity`, `questionnaire_format`.

Validator statuses: `pass`, `retry`, `manual_review`, `failed`.

## Role responsibilities

- **Router:** detect/rank no repairs; accept clean items, route one clear supported
  defect to its canonical family, and use fallback for multi-label, low-confidence,
  conflicting, unsupported, or ambiguous cases.
- **Planner:** translate the fixed routed issue set into a minimal family/agent plan;
  never add or remove labels and never rewrite the item.
- **Specialists:** repair only their routed family and preserve all unrelated content.
- **Fallback reviser:** coordinate independently supported multi-label repairs and
  behave conservatively under uncertainty or unsupported evidence.
- **Validator:** evaluate rather than rewrite; distinguish `pass`, focused `retry`,
  `manual_review`, and the narrow unevaluable `failed` condition. On the clean path,
  `fixes_detected_issue` is exactly `null`; with detected issues it is boolean.

## P2 demonstration scope

| Runtime role | Examples | Targeted behavior |
| --- | ---: | --- |
| Baseline quality checker | 4 | Overlap-only detection; agreement proxy; independently supported long-scale labels; clean acceptance |
| Baseline item reviser | 4 | Minimal overlap repair; item-specific scale; coordinated long-scale repair; exact clean preservation |
| Orchestration router | 5 | Single-label option routing; agreement routing; format routing; multi-label fallback; clean acceptance |
| Fallback reviser | 3 | Same-family multi-label repair; low-confidence restraint; unchanged unsupported repair |
| Response-options specialist | 5 | Overlap repair; agreement repair; polarity/dimension repair; rejection of speculative completeness; scale balance |
| Questionnaire-format specialist | 2 | Open narrative paired with fixed rating; exact-entry request paired with grouped ranges |
| Validator | 5 | Clean pass/null; repaired-issue pass/true; retry; manual review; failed/unavailable candidate |
| Planner, wording, construct, bias | 0 | No P2 demonstration; zero-shot role rules retained |

The P2 questions and constructs were independently authored outside the v4 200-item
benchmark. The package validation report records exact-match and lexical/character
similarity checks. Structural resemblance such as an overlapping numeric boundary is
intentional because P2 is specifically a response-option calibration treatment; the
wording, domain, and construct are independent.

## Model-facing data boundary

Prompts may receive only the visible question, response options, and runtime-generated
issue/routing/revision context. They must not expose benchmark item IDs, gold labels,
expected revisions, topics, target concepts, metadata, or review notes.
