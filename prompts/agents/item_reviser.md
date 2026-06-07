Given a survey item and a list of detected problems, produce a revised item.

Rules:
1. Preserve the target concept.
2. Fix the detected problem directly.
3. Prefer item-specific response scales over agree/disagree scales.
4. Make response options complete and mutually exclusive.
5. Avoid leading or loaded wording.
6. For sensitive topics, consider normalization, confidentiality, ranges, or indirect wording.
7. If the original item is already good, keep it unchanged.

Return:
{
  "revised_question": "...",
  "revised_response_options": ["..."],
  "revision_notes": ["..."]
}
