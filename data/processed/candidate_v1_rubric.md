# Candidate v1 Benchmark Rubric

This rubric defines the candidate_v1 benchmark logic for the item-reviser only. It paraphrases the first six chapters of Saris and Gallhofer (2014) and the local seminar materials; it is not a final gold-codebook.

## Source-Grounded Design Logic

- Preserve the target concept. A revision may improve wording only if it still measures the same concept-by-intuition or the same intended indicator of a concept-by-postulation.
- Make the assertion behind the request clear. The item should make it easy to see what subject, object, predicate, time reference, and condition are being measured.
- Keep one request tied to one concept unless a carefully justified composite measure is intended. Ordinary double-barreled items should be split.
- Make assumptions explicit. If a follow-up only applies to respondents with an experience or behavior, use a filter structure.
- Match the response space to the request. Closed categories should fit the concept, be complete, be mutually exclusive for single-choice items, and use suitable labels or reference points.
- Choose open-ended items when the benchmarked measurement goal is a reason, explanation, top-of-mind problem, or other answer not known in advance.
- Prefer item-specific response options over agree-disagree translations when the item is trying to place respondents on a substantive dimension such as support, satisfaction, frequency, intensity, or evaluation.
- Reduce avoidable response burden: keep reference periods realistic, define unclear terms before the request, avoid unnecessary subordinate clauses, and avoid negative or double-negative wording.
- Treat sensitive and socially desirable behaviors with lower-threat wording, bounded reference periods, neutral context, and a nonresponse option where appropriate.
- Do not overcorrect clean controls. Some clean items are deliberately simple, and some are nuanced but acceptable.

## Label Adjudication Rules

| Label | Candidate trigger | Preferred correction |
|---|---|---|
| `leading_question` | Stem signals a preferred answer or says one answer is normal/responsible. | Reword neutrally and use balanced options. |
| `loaded_question` | Stem assumes an event, behavior, attitude, or status that may not apply. | Add a filter or explicit none/not applicable path. |
| `double_barreled` | One item asks about two separable concepts, objects, or behaviors. | Split into separate items; keep each response scale aligned. |
| `recall_error` | Reference period is too long or vague for the behavior being recalled. | Use a shorter, specific reference period or a usual-behavior frame. |
| `vague_ambiguous` | Key concept, object, actor, time, or scale meaning is unclear. | Define the term and specify the target behavior, service, or period. |
| `sensitive_topic_direct` | Sensitive behavior is asked abruptly without threat reduction. | Normalize lightly, bound time, and include `Prefer not to answer` where suitable. |
| `social_desirability` | Wording invokes moral norms, good citizenship, honesty, responsibility, or shame. | Remove normative pressure and ask the behavior neutrally. |
| `negative_wording` | Negatives or double negatives make the direction hard to process. | Recast positively or directly. |
| `open_closed_mismatch` | Open answer is needed but closed options are supplied, or a closed decision is requested without options. | Match open/closed structure to the measurement goal. |
| `agree_disagree_scale` | Agree-disagree format is used where an item-specific scale is clearer. | Replace with support, satisfaction, frequency, evaluation, or other construct-specific options. |
| `unbalanced_scale` | A bipolar construct gives more weight to one side or omits the opposite side. | Use symmetric categories around a neutral point when applicable. |
| `incomplete_options` | A closed list omits plausible respondent states. | Add missing categories or an appropriate residual option. |
| `non_exclusive_options` | Single-choice categories overlap. | Use non-overlapping categories or allow multiple selection if that is the intended task. |
| `missing_scale_labels` | Numeric points lack enough labels or fixed reference points. | Label endpoints and important anchors. |
| `too_many_scale_points` | The item asks for more precision than most respondents can use reliably for the benchmarked construct. | Use a shorter labeled scale unless high precision is justified. |
| `polarity_mismatch` | The concept and response scale point in different semantic directions. | Use options that express the same polarity as the stem. |

## Candidate Review Guidance

Human reviewers should check whether each row has the right label set, whether the expected revision preserves the target concept, whether multi-label combinations are realistic, and whether the clean controls are truly clean enough for false-positive testing.
