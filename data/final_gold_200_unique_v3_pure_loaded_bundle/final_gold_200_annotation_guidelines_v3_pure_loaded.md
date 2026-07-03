# Annotation Guidelines for `final_gold_200_unique_v3_pure_loaded`

This benchmark tests whether a model can detect questionnaire-quality flaws and optionally produce construct-preserving revisions.

## General decision rules

1. Preserve the target construct when revising an item.
2. Do not add new constructs to the revision.
3. For multi-label rows, the revision should address all annotated flaws.
4. Clean controls should not be rewritten unless a genuine defect is detected.
5. Sensitive items should include respectful framing and a nonresponse option where appropriate.
6. For single-label rows, avoid adding a second independently valid flaw through the response options.

## Label definitions

### `leading_question`
Question wording cues a preferred answer through agreement prompts, persuasive premises, or directional phrasing.

### `loaded_question`
Question contains judgmental, accusatory, or presuppositional wording that distorts the response task. In single-label `loaded_question` rows, the defect should be located in the stem, not in an omitted `No`, `Never`, `0`, residual, or not-applicable response category.

### `double_barreled`
One item asks about two or more separable constructs that could receive different answers.

### `recall_error`
Reference period or memory demand is too long, vague, or unsuitable for the behavior being measured.

### `vague_ambiguous`
Key terms, target concept, reference period, population, or requested judgment are underspecified.

### `sensitive_topic_direct`
Sensitive behavior or status is asked too directly without softening, normalization, or a nonresponse option.

### `social_desirability`
Question wording invokes social approval, duty, morality, or desirable identity that pressures respondents.

### `negative_wording`
Negations or double negatives make the response direction difficult to interpret.

### `open_closed_mismatch`
The wording asks for an open response but gives closed options, or asks a closed question without matching closed options.

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

## Composition

- 40 clean controls
- 128 single-label flawed items, 8 per flaw label
- 32 multi-label flawed items
- 12 total appearances for every flaw label
