Given a survey item, identify questionnaire-design problems.

Check at least:
- leading wording
- loaded assumptions
- double-barreled wording
- recall difficulty
- vague or ambiguous wording
- sensitive topics and social desirability
- negative wording or double negatives
- open/closed mismatch
- agree/disagree scale problems
- unbalanced response categories
- incomplete or non-exclusive categories
- missing labels
- too many scale points
- polarity mismatch

Return:
{
  "errors": [
    {
      "category": "...",
      "severity": "low|medium|high",
      "explanation": "...",
      "evidence": "..."
    }
  ]
}
