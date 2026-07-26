# Phase Reasoning for final_gold_200_unique_v4_professor_review

## Phase 1: Separate wording defects from annotation defects

The professor’s review identifies six clean controls whose response tasks are not sufficiently consistent or quantified, plus flawed items with missing secondary labels.

## Phase 2: Repair clean controls without changing their constructs

Items003, 013, and 040 were converted to count-only categories. Items007, 008, and 027 were rewritten to use explicit opportunity-based rates or proportions. Their expected revisions remain identical, so they continue to function as clean controls.

## Phase 3: Strengthen intended flaw examples

Item110 was changed from a defensible open-ended item into a clear mismatch: the stem requests an explanation, but the response field contains closed categories only.

## Phase 4: Add independently valid labels

- `vague_ambiguous`: Items090–093
- `agree_disagree_scale`: Item100
- `missing_scale_labels`: Items153–160
- `negative_wording`: Item191

Expected revisions and revision notes were checked to ensure that every added label is addressed.

## Phase 5: Revalidate structure and diversity

The dataset remains 200 rows with 40 clean controls and 160 flawed rows. All clean revisions are identical, there are no exact duplicate questions, and no pair reaches the 0.72 normalized similarity threshold.

## Phase 6: Accept natural label imbalance

The reviewed version no longer enforces exactly 12 appearances per label. That balance would require deleting valid annotations or redesigning unrelated rows. This version therefore treats annotation validity as the higher-priority criterion.
