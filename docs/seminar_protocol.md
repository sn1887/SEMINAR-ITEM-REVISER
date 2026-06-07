# Shared Meeting Protocol Adapted for This Repository

This file mirrors the protocol structure you pasted into the chat. Use it before and after meetings with Bolei and Caro.

## Purpose

Document progress, open questions, decisions, and next steps for the **Item Reviser Agent**.

## How to use

Before each meeting:

1. Run the current evaluation.
2. Add a short progress note.
3. Add concrete questions where Bolei/Caro input is needed.
4. Record decisions immediately after the meeting.

---

# Meeting Log

| Date | Participants | Main topics | Key decisions | Next steps |
|---|---|---|---|---|
| TBD | Solo student, Bolei, Caro | Repo setup, evaluation set, error taxonomy | TBD | TBD |

---

# 1. Progress on Technical Set-up on LRZ

## Current status

- LRZ login works.
- Shared storage access has been verified.
- Repository is designed to keep model paths flexible.
- Mock backend runs locally without GPUs.

## Completed tasks

- Created Hydra-based repo structure.
- Added 200-item seed evaluation set.
- Added deterministic baseline checks.
- Added evaluation runner and report generation.

## Issues or blockers

- Need to test one real local model on LRZ.
- Need to decide whether to use Hugging Face direct loading or vLLM/OpenAI-compatible server for benchmarking.

## Questions for Bolei and Caro

1. Which local model should be used first for the initial benchmark?
2. Should the final evaluation include only local open-source models, or also API models?
3. Is it acceptable to use a rule-based baseline as one comparison system?

## Decisions made

- TBD.

---

# 2. Progress on Design of the Agent

## Current status

The agent is designed as a quality-checking and revision loop:

```text
Survey item
  -> quality checker(s)
  -> combined feedback
  -> item reviser
  -> revised survey item
```

## Prompting strategy

The planned LLM prompt asks the model to:

1. identify item-design errors,
2. explain each error,
3. propose a revised item,
4. avoid overcorrecting items that are already valid,
5. preserve the target concept.

A deterministic baseline is included so that evaluation can begin before GPU/model decisions are finalized.

## Questions for Bolei and Caro

1. Should the item reviser return one best revision or multiple alternatives?
2. Should it revise both wording and scale in the same step?
3. Should the quality checker and reviser be separate agents in the final system?
4. Should the final output include confidence scores?

## Decisions made

- TBD.

---

# 3. Progress on Design of Evaluation and Creation of Test Data

## Current status

- A 200-item seed dataset exists at `data/eval/test_set_200_seed.jsonl`.
- It contains flawed items and clean control items.
- Categories include leading, loaded, recall, vague wording, sensitive topics, scale problems, agree/disagree scales, and overcorrection controls.

## Evaluation goals

- Detect real item-design errors.
- Avoid overcorrecting valid items.
- Produce useful improved items.
- Preserve the intended concept.
- Avoid introducing new problems.

## Evaluation criteria or metrics

Automatic baseline metrics:

- category-level precision,
- category-level recall,
- F1,
- exact match of error set,
- false positive rate on clean items,
- overcorrection rate.

Manual evaluation criteria:

- Was the flagged issue real?
- Was the explanation correct?
- Did the revision preserve the target concept?
- Did the revision remove the original problem?
- Did the revision introduce a new problem?

## Test data

Current seed set: 200 items.

Recommended next steps:

1. Audit all category labels.
2. Mark 20–30 ambiguous items for discussion.
3. Confirm which categories belong in the final taxonomy.
4. Freeze a `v1` gold dataset.

## Questions for Bolei and Caro

1. Is 200 items enough for the interim evaluation?
2. How many clean controls should be included to measure overcorrection?
3. Should each item have exactly one primary error, or can it have multiple labels?
4. Should we include examples from real questionnaires, or only synthetic examples?
5. Should revisions be evaluated manually, automatically, or both?

## Decisions made

- TBD.
