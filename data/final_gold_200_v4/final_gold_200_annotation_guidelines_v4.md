# Annotation Guidelines for `final_gold_200_unique_v4_professor_review`

This benchmark tests whether a model can detect questionnaire-quality flaws and produce construct-preserving revisions.

## General decision rules

1. Preserve the target construct when revising an item.
2. Annotate every independently defensible flaw; do not suppress a label merely to maintain class balance.
3. For multi-label rows, the revision should address all annotated flaws.
4. Clean controls should have an identical expected revision.
5. Sensitive items should use respectful framing and a nonresponse option where appropriate.
6. Distinguish vague quantification from ordinary frequency measurement: counts, rates, proportions, reference periods, and denominators should be explicit enough to interpret consistently.
7. Numeric scales require interpretable direction/endpoints; excessive precision and missing labels can co-occur.
8. Agreement scales should be labeled `agree_disagree_scale` when item-specific categories would measure the construct more directly.

## Label definitions

### `leading_question`
Question wording cues a preferred answer through agreement prompts, persuasive premises, or directional phrasing.

### `loaded_question`
Question contains judgmental, accusatory, or presuppositional wording that distorts the response task.

### `double_barreled`
One item asks about two or more separable constructs that could receive different answers.

### `recall_error`
Reference period or memory demand is too long, vague, or unsuitable for the behavior being measured.

### `vague_ambiguous`
Key terms, target event, reference period, denominator, population, or requested judgment are underspecified.

### `sensitive_topic_direct`
Sensitive behavior or status is asked too directly without softening, normalization, or a nonresponse option.

### `social_desirability`
Question wording invokes social approval, duty, morality, or desirable identity that pressures respondents.

### `negative_wording`
Negations, negatively framed predicates, or double negatives make the response task/direction harder to interpret.

### `open_closed_mismatch`
The wording requests an open response but the response field only permits closed categories, or vice versa.

### `agree_disagree_scale`
Agreement options are used to measure a construct that should be asked with item-specific response categories.

### `unbalanced_scale`
The response scale gives more intensity points to one side of the construct than the other.

### `incomplete_options`
Closed categories omit plausible respondent cases or lack residual/nonresponse options where needed.

### `non_exclusive_options`
Closed categories overlap, so a respondent could legitimately select more than one answer.

### `missing_scale_labels`
Numeric or short verbal scale points lack labels needed to interpret direction, midpoint, or endpoints.

### `too_many_scale_points`
The item asks for more scale precision than respondents can meaningfully distinguish for the construct.

### `polarity_mismatch`
The response options measure a different polarity or construct from the wording of the question.

## Current composition

- 40 clean controls
- 115 single-label flawed items
- 45 multi-label flawed items
- Natural, review-driven label frequencies rather than exact equal exposure

See the summary and validation JSON for per-label counts.
