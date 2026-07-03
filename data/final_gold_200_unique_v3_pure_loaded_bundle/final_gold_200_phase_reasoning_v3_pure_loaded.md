# Phase Reasoning for final_gold_200_unique_v3_pure_loaded

## Phase 1: Diagnose the residual weakness

The v2 benchmark solved most template-duplication problems, but the single-label `loaded_question` rows still risked label contamination because the response options often omitted a no-event category. That made `incomplete_options` a methodologically reasonable extra label.

## Phase 2: Define the repair criterion

A single-label `loaded_question` row should be flawed because the stem is presuppositional, accusatory, or judgmental. The response options should not independently create a second flaw.

## Phase 3: Rewrite loaded-question rows

The eight single-label rows were rewritten across everyday contexts and varied response formats. The four multi-label loaded rows were also patched so they preserve their intended multi-label status without accidentally introducing `incomplete_options` as a third label.

## Phase 4: Validate structure and diversity

The validation pass checked row counts, clean/flawed split, single/multi-label balance, exact label exposures, topic and format distributions, duplicate questions, repeated openings, pairwise similarity, clean-control revision consistency, and the focused loaded-question purity audit.

## Phase 5: Result

The resulting file keeps the v2 structural strengths and addresses the taxonomy issue raised in review. It is suitable as a stronger seminar benchmark candidate, subject to final human/professor signoff.
