# Literature-Derived Checklist for the Item Reviser

This checklist translates the seminar readings and slides into implementable checks.

## Core reading task

Read the first four chapters of Saris & Gallhofer carefully and extract rules for:

1. concepts-by-intuition vs concepts-by-postulation,
2. assertions,
3. requests for answers,
4. problematic requests and design choices.

## Concept preservation

A revision is not good if it fixes wording but changes the target concept.

Example:

```text
Bad target: policy of government intervention
Bad item: Is private enterprise the best way to solve our economic problems?
Better direction: Should the government intervene to solve economic problems?
```

## Error categories to check

### Wording

- leading wording,
- loaded assumptions,
- double-barreled requests,
- vague or ambiguous wording,
- recall burden,
- sensitive topics,
- social desirability,
- negative wording and double negatives.

### Scale

- response options do not match request,
- incomplete categories,
- non-exclusive categories,
- unbalanced categories,
- missing labels,
- too many points,
- wrong polarity,
- agree/disagree where item-specific scales are preferable.

## Special concern: overcorrection

The evaluation must include valid questions with no error. Otherwise, the agent may learn to always revise. The final evaluation should explicitly measure false positives and unnecessary rewrites.

## Notes for prompt design

The agent should be instructed to:

- preserve target concept,
- separate detection from revision,
- return structured JSON,
- avoid unnecessary rewriting,
- revise response options if scale is the problem,
- state uncertainty when the item is ambiguous.
