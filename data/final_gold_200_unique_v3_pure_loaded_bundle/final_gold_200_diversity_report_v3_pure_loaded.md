# final_gold_200_unique_v3_pure_loaded Diversity and Template-Risk Report

## Template checks

| Metric | Result |
|---|---:|
| Rows | 200 |
| Exact duplicate questions | 0 |
| Max repeated 5-word opening stem | 3 |
| Pairwise similarity threshold | 0.72 |
| Pairwise similarity pairs above threshold | 0 |
| Maximum pairwise normalized similarity | 0.7083 |
| Max repeated option set | 23 |

## Most common 5-word openings

| Opening | Count |
|---|---:|
| `in the past 7 days` | 3 |
| `how satisfied or dissatisfied are` | 3 |
| `please rate your concern about` | 3 |
| `do you support or oppose` | 3 |
| `how much control do you` | 2 |
| `what is the main reason` | 2 |
| `which mode of transport do` | 2 |
| `how fair or unfair do` | 2 |
| `during the last 3 months` | 2 |
| `in the past 12 months` | 2 |

## Loaded-question diversity after cleanup

The single-label loaded-question rows now use varied mechanisms and response formats rather than one frequency-without-zero template.

| ID | Topic | Format | Question | Coverage note |
|---|---|---|---|---|
| `gold-200-rewritten-049` | finances | `ordinal_categories` | How much did the bank's hidden account fees reduce the money you had available for monthly expenses? | neutral/no-event/balanced response path included |
| `gold-200-rewritten-050` | university life | `open_ended` | In what ways did the confusing course registration portal make it harder for you to plan this semester? | open-ended response |
| `gold-200-rewritten-051` | technology | `frequency` | During the last month, how often did the campus app's recurring login problems prevent you from accessing university services? | neutral/no-event/balanced response path included |
| `gold-200-rewritten-052` | labor | `numeric_ranges` | Last month, how much extra time did the poorly organized shift-scheduling system create for you? | neutral/no-event/balanced response path included |
| `gold-200-rewritten-053` | family/household | `categorical_closed_ended` | Which household task, if any, was most affected by your building's unreliable maintenance service this winter? | neutral/no-event/balanced response path included |
| `gold-200-rewritten-054` | mobility | `ordinal_categories` | What effect did the city's poorly timed roadworks have on your usual commute last week? | neutral/no-event/balanced response path included |
| `gold-200-rewritten-055` | politics/public policy | `support_oppose` | Do you support or oppose reducing the city's excessive spending on decorative public signs? | neutral/no-event/balanced response path included |
| `gold-200-rewritten-056` | health | `binary_yes_no` | This year, did the clinic's confusing appointment reminders cause you to miss or reschedule an appointment? | neutral/no-event/balanced response path included |

## Multi-label loaded-question rows

The four multi-label loaded rows remain intentionally multi-label. Two are paired with `sensitive_topic_direct`, and two are paired with `open_closed_mismatch`. Their v3 versions include no-event or refusal paths where appropriate so that `incomplete_options` is not accidentally encouraged as an unannotated extra label.
