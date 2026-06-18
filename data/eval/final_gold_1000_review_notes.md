# final_gold_1000 Review Notes

## Review workflow used
- Source/Rubric Auditor
- Schema and Integrity Auditor
- Clean-Control Reviewer
- Single-Label Taxonomy Reviewers
- Multi-Label Reviewer
- Coverage and Balance Auditor

## Clean-control decision criteria
- Select clean rows that are genuinely acceptable, cover topics/format variation, and do not introduce correction risk.
- Total selected: 200

## Single-label criteria
- For each taxonomy label, require clear flaw presence and minimal correction that preserves target concept.
- Apply fixed quota (40) per label.

- `leading_question`: selected 40; first skipped: `candidate-v1-single-leading-question-041`, `candidate-v1-single-leading-question-042`, `candidate-v1-single-leading-question-043`, `candidate-v1-single-leading-question-044`, `candidate-v1-single-leading-question-045`
- `loaded_question`: selected 40; first skipped: `candidate-v1-single-loaded-question-041`, `candidate-v1-single-loaded-question-042`, `candidate-v1-single-loaded-question-043`, `candidate-v1-single-loaded-question-044`, `candidate-v1-single-loaded-question-045`
- `double_barreled`: selected 40; first skipped: `candidate-v1-single-double-barreled-041`, `candidate-v1-single-double-barreled-042`, `candidate-v1-single-double-barreled-043`, `candidate-v1-single-double-barreled-044`, `candidate-v1-single-double-barreled-045`
- `recall_error`: selected 40; first skipped: `candidate-v1-single-recall-error-041`, `candidate-v1-single-recall-error-042`, `candidate-v1-single-recall-error-043`, `candidate-v1-single-recall-error-044`, `candidate-v1-single-recall-error-045`
- `vague_ambiguous`: selected 40; first skipped: `candidate-v1-single-vague-ambiguous-041`, `candidate-v1-single-vague-ambiguous-042`, `candidate-v1-single-vague-ambiguous-043`, `candidate-v1-single-vague-ambiguous-044`, `candidate-v1-single-vague-ambiguous-045`
- `sensitive_topic_direct`: selected 40; first skipped: `candidate-v1-single-sensitive-topic-direct-041`, `candidate-v1-single-sensitive-topic-direct-042`, `candidate-v1-single-sensitive-topic-direct-043`, `candidate-v1-single-sensitive-topic-direct-044`, `candidate-v1-single-sensitive-topic-direct-045`
- `social_desirability`: selected 40; first skipped: `candidate-v1-single-social-desirability-041`, `candidate-v1-single-social-desirability-042`, `candidate-v1-single-social-desirability-043`, `candidate-v1-single-social-desirability-044`, `candidate-v1-single-social-desirability-045`
- `negative_wording`: selected 40; first skipped: `candidate-v1-single-negative-wording-041`, `candidate-v1-single-negative-wording-042`, `candidate-v1-single-negative-wording-043`, `candidate-v1-single-negative-wording-044`, `candidate-v1-single-negative-wording-045`
- `open_closed_mismatch`: selected 40; first skipped: `candidate-v1-single-open-closed-mismatch-041`, `candidate-v1-single-open-closed-mismatch-042`, `candidate-v1-single-open-closed-mismatch-043`, `candidate-v1-single-open-closed-mismatch-044`, `candidate-v1-single-open-closed-mismatch-045`
- `agree_disagree_scale`: selected 40; first skipped: `candidate-v1-single-agree-disagree-scale-041`, `candidate-v1-single-agree-disagree-scale-042`, `candidate-v1-single-agree-disagree-scale-043`, `candidate-v1-single-agree-disagree-scale-044`, `candidate-v1-single-agree-disagree-scale-045`
- `unbalanced_scale`: selected 40; first skipped: `candidate-v1-single-unbalanced-scale-041`, `candidate-v1-single-unbalanced-scale-042`, `candidate-v1-single-unbalanced-scale-043`, `candidate-v1-single-unbalanced-scale-044`, `candidate-v1-single-unbalanced-scale-045`
- `incomplete_options`: selected 40; first skipped: `candidate-v1-single-incomplete-options-041`, `candidate-v1-single-incomplete-options-042`, `candidate-v1-single-incomplete-options-043`, `candidate-v1-single-incomplete-options-044`, `candidate-v1-single-incomplete-options-045`
- `non_exclusive_options`: selected 40; first skipped: `candidate-v1-single-non-exclusive-options-041`, `candidate-v1-single-non-exclusive-options-042`, `candidate-v1-single-non-exclusive-options-043`, `candidate-v1-single-non-exclusive-options-044`, `candidate-v1-single-non-exclusive-options-045`
- `missing_scale_labels`: selected 40; first skipped: `candidate-v1-single-missing-scale-labels-041`, `candidate-v1-single-missing-scale-labels-042`, `candidate-v1-single-missing-scale-labels-043`, `candidate-v1-single-missing-scale-labels-044`, `candidate-v1-single-missing-scale-labels-045`
- `too_many_scale_points`: selected 40; first skipped: `candidate-v1-single-too-many-scale-points-041`, `candidate-v1-single-too-many-scale-points-042`, `candidate-v1-single-too-many-scale-points-043`, `candidate-v1-single-too-many-scale-points-044`, `candidate-v1-single-too-many-scale-points-045`
- `polarity_mismatch`: selected 40; first skipped: `candidate-v1-single-polarity-mismatch-041`, `candidate-v1-single-polarity-mismatch-042`, `candidate-v1-single-polarity-mismatch-043`, `candidate-v1-single-polarity-mismatch-044`, `candidate-v1-single-polarity-mismatch-045`

## Multi-label criteria
- Select 10 examples per designed two-label combination for realistic but controlled multi-label coverage.
- This yields 20 appearances per label in multi-label set (2 combinations × 10 each).
- `agree_disagree_scale+negative_wording`: skipped beyond quota: `candidate-v1-multi-agree-disagree-scale-negative-wording-011`, `candidate-v1-multi-agree-disagree-scale-negative-wording-012`, `candidate-v1-multi-agree-disagree-scale-negative-wording-013`, `candidate-v1-multi-agree-disagree-scale-negative-wording-014`
- `double_barreled+leading_question`: skipped beyond quota: `candidate-v1-multi-double-barreled-leading-question-011`, `candidate-v1-multi-double-barreled-leading-question-012`, `candidate-v1-multi-double-barreled-leading-question-013`, `candidate-v1-multi-double-barreled-leading-question-014`
- `incomplete_options+non_exclusive_options`: skipped beyond quota: `candidate-v1-multi-incomplete-options-non-exclusive-options-011`, `candidate-v1-multi-incomplete-options-non-exclusive-options-012`, `candidate-v1-multi-incomplete-options-non-exclusive-options-013`, `candidate-v1-multi-incomplete-options-non-exclusive-options-014`
- `leading_question+unbalanced_scale`: skipped beyond quota: `candidate-v1-multi-leading-question-unbalanced-scale-011`, `candidate-v1-multi-leading-question-unbalanced-scale-012`, `candidate-v1-multi-leading-question-unbalanced-scale-013`, `candidate-v1-multi-leading-question-unbalanced-scale-014`
- `loaded_question+sensitive_topic_direct`: skipped beyond quota: `candidate-v1-multi-loaded-question-sensitive-topic-direct-011`, `candidate-v1-multi-loaded-question-sensitive-topic-direct-012`, `candidate-v1-multi-loaded-question-sensitive-topic-direct-013`, `candidate-v1-multi-loaded-question-sensitive-topic-direct-014`
- `missing_scale_labels+too_many_scale_points`: skipped beyond quota: `candidate-v1-multi-missing-scale-labels-too-many-scale-points-011`, `candidate-v1-multi-missing-scale-labels-too-many-scale-points-012`, `candidate-v1-multi-missing-scale-labels-too-many-scale-points-013`, `candidate-v1-multi-missing-scale-labels-too-many-scale-points-014`
- `negative_wording+polarity_mismatch`: skipped beyond quota: `candidate-v1-multi-negative-wording-polarity-mismatch-011`, `candidate-v1-multi-negative-wording-polarity-mismatch-012`, `candidate-v1-multi-negative-wording-polarity-mismatch-013`, `candidate-v1-multi-negative-wording-polarity-mismatch-014`
- `non_exclusive_options+open_closed_mismatch`: skipped beyond quota: `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-011`, `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-012`, `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-013`, `candidate-v1-multi-non-exclusive-options-open-closed-mismatch-014`
- `open_closed_mismatch+loaded_question`: skipped beyond quota: `candidate-v1-multi-open-closed-mismatch-loaded-question-011`, `candidate-v1-multi-open-closed-mismatch-loaded-question-012`, `candidate-v1-multi-open-closed-mismatch-loaded-question-013`, `candidate-v1-multi-open-closed-mismatch-loaded-question-014`
- `polarity_mismatch+incomplete_options`: skipped beyond quota: `candidate-v1-multi-polarity-mismatch-incomplete-options-011`, `candidate-v1-multi-polarity-mismatch-incomplete-options-012`, `candidate-v1-multi-polarity-mismatch-incomplete-options-013`, `candidate-v1-multi-polarity-mismatch-incomplete-options-014`
- `recall_error+double_barreled`: skipped beyond quota: `candidate-v1-multi-recall-error-double-barreled-011`, `candidate-v1-multi-recall-error-double-barreled-012`, `candidate-v1-multi-recall-error-double-barreled-013`, `candidate-v1-multi-recall-error-double-barreled-014`
- `sensitive_topic_direct+social_desirability`: skipped beyond quota: `candidate-v1-multi-sensitive-topic-direct-social-desirability-011`, `candidate-v1-multi-sensitive-topic-direct-social-desirability-012`, `candidate-v1-multi-sensitive-topic-direct-social-desirability-013`, `candidate-v1-multi-sensitive-topic-direct-social-desirability-014`
- `social_desirability+vague_ambiguous`: skipped beyond quota: `candidate-v1-multi-social-desirability-vague-ambiguous-011`, `candidate-v1-multi-social-desirability-vague-ambiguous-012`, `candidate-v1-multi-social-desirability-vague-ambiguous-013`, `candidate-v1-multi-social-desirability-vague-ambiguous-014`
- `too_many_scale_points+agree_disagree_scale`: skipped beyond quota: `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-011`, `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-012`, `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-013`, `candidate-v1-multi-too-many-scale-points-agree-disagree-scale-014`
- `unbalanced_scale+missing_scale_labels`: skipped beyond quota: `candidate-v1-multi-unbalanced-scale-missing-scale-labels-011`, `candidate-v1-multi-unbalanced-scale-missing-scale-labels-012`, `candidate-v1-multi-unbalanced-scale-missing-scale-labels-013`, `candidate-v1-multi-unbalanced-scale-missing-scale-labels-014`
- `vague_ambiguous+recall_error`: skipped beyond quota: `candidate-v1-multi-vague-ambiguous-recall-error-011`, `candidate-v1-multi-vague-ambiguous-recall-error-012`, `candidate-v1-multi-vague-ambiguous-recall-error-013`, `candidate-v1-multi-vague-ambiguous-recall-error-014`

## Expected revision checks performed
- Expected revisions retained from source; no row rewrites were performed in this curation pass.
- Concept alignment and format fixes were not rewritten, preserving construct validity while keeping a consistent benchmark reference.

## Remaining human attention items
- Re-check open-closed mismatch rows for openness/anchoring consistency after scoring integration.
- Validate if synthetic clean controls with added context suffixes could inflate readability compared with field versions.
- Spot-check sensitive-topic rows for ethical neutrality and threat-reduction tone in target deployment context.
