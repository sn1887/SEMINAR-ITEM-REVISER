# Agent Prompt Layout

Prompt bodies are separated by runtime path:

- `baseline/`: prompts used by the default non-orchestrated pipeline when
  `orchestration.enabled=false`.
- `orchestration/`: prompts used by the opt-in router, planner, specialist,
  fallback, and validator workflow when `orchestration.enabled=true`.

The active prompt slots and file paths are configured in
`configs/prompt/default.yaml`.
