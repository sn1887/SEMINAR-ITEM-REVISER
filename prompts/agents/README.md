# Agent Prompt Layout

Prompt bodies are separated by runtime path:

- `baseline/`: prompts used by the default non-orchestrated pipeline when
  `orchestration.enabled=false`.
- `baseline_codebook/`: opt-in zero-shot prompts with embedded taxonomy boundary
  rules and conservative multi-label instructions.
- `orchestration/`: prompts used by the opt-in router, planner, specialist,
  fallback, and validator workflow when `orchestration.enabled=true`.
- `orchestration_codebook/`: opt-in orchestration router/fallback prompts with
  codebook-based detection and clean-item guardrails.
- `baseline_p1/` and `orchestration_p1/`: additive P1 prompts that preserve the
  relevant P0 codebook content and append operational response-option rules.
- `baseline_p2/` and `orchestration_p2/`: additive P2 prompts that preserve P1
  and append fixed calibration examples authored from general survey-design
  principles.

The active prompt slots and file paths are configured in
`configs/prompt/default.yaml`. Select variants with Hydra, for example
`prompt=baseline_codebook` or `prompt=orchestration_codebook`.
