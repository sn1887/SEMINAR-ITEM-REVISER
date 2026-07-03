# final_gold_200_unique_v2 Phase Reasoning

## Phase 1 — Audit the 1,000-item source pool

The source pool was first treated as a seed pool rather than a finished benchmark. The audit checked row-type balance, label counts, topic and response-format coverage, repeated openings, repeated option banks, and near-template risk. The source was numerically balanced but had strong wording regularities, so direct downsampling was rejected.

## Phase 2 — Fix the 200-item target matrix

The final matrix was set to 40 clean controls, 128 single-label flawed items, and 32 multi-label flawed items. Every one of the 16 flaw labels appears exactly 12 times: 8 single-label rows and 4 appearances inside multi-label rows.

## Phase 3 — Select seeds with traceability

Each final item keeps a source seed identifier from the 1,000-item file. Seeds were selected to cover labels and formats while avoiding a simple first-N quota selection.

## Phase 4 — Rewrite for uniqueness

The final questions were rewritten with varied topics, populations, time windows, and response tasks. The rewrite objective was to preserve the intended flaw while making the surface form less template-like.

## Phase 5 — Rewrite expected revisions

Every flawed item has an expected revision that fixes the known error or errors while preserving the target concept. Clean controls were synchronized so their expected revision exactly matches the clean item.

## Phase 6 — Validate the artifact

Validation confirmed 200 rows, no duplicate IDs, no duplicate final questions, all clean-control revisions identical to the question, and exact label exposure of 12 per flaw label. The final similarity audit found 0 question pairs above 0.72 normalized similarity; these are documented in the diversity report for manual review.
