# Loaded-question Cleanup Report

## Problem addressed

In v2, the single-label `loaded_question` rows often looked like frequency questions with only positive-frequency answers. That made `incomplete_options` a defensible extra diagnosis. v3 rewrites the loaded rows so the flaw is in the wording premise, not the response coverage.

## Patched loaded-question rows

| ID | Gold labels | Topic | Format | Question | Expected revision question |
|---|---|---|---|---|---|
| `gold-200-rewritten-049` | `loaded_question` | finances | `ordinal_categories` | How much did the bank's hidden account fees reduce the money you had available for monthly expenses? | During the last 12 months, how much did account fees, if any, affect the money you had available for monthly expenses? |
| `gold-200-rewritten-050` | `loaded_question` | university life | `open_ended` | In what ways did the confusing course registration portal make it harder for you to plan this semester? | In what ways, if any, did the course registration portal affect your ability to plan this semester? |
| `gold-200-rewritten-051` | `loaded_question` | technology | `frequency` | During the last month, how often did the campus app's recurring login problems prevent you from accessing university services? | During the last month, how often, if at all, did login problems with the campus app prevent you from accessing university services? |
| `gold-200-rewritten-052` | `loaded_question` | labor | `numeric_ranges` | Last month, how much extra time did the poorly organized shift-scheduling system create for you? | Last month, how much extra time, if any, did the shift-scheduling system create for you? |
| `gold-200-rewritten-053` | `loaded_question` | family/household | `categorical_closed_ended` | Which household task, if any, was most affected by your building's unreliable maintenance service this winter? | This winter, did building maintenance service affect any household task? If yes, which task was most affected? |
| `gold-200-rewritten-054` | `loaded_question` | mobility | `ordinal_categories` | What effect did the city's poorly timed roadworks have on your usual commute last week? | Last week, what effect, if any, did the city's roadworks have on your usual commute? |
| `gold-200-rewritten-055` | `loaded_question` | politics/public policy | `support_oppose` | Do you support or oppose reducing the city's excessive spending on decorative public signs? | Do you support or oppose reducing city spending on decorative public signs? |
| `gold-200-rewritten-056` | `loaded_question` | health | `binary_yes_no` | This year, did the clinic's confusing appointment reminders cause you to miss or reschedule an appointment? | This year, did appointment reminders from a clinic cause you to miss or reschedule an appointment? |
| `gold-200-rewritten-177` | `loaded_question;sensitive_topic_direct` | sensitive behaviors | `filter_question` | How much did using drugs not legally available to you interfere with your class or work attendance during the last 12 months? | This item is optional. During the last 12 months, did you use drugs not legally available to you? If yes, how much, if at all, did this interfere with your class or work attendance? |
| `gold-200-rewritten-178` | `loaded_question;sensitive_topic_direct` | education | `filter_question` | How much did paying someone to complete coursework for you improve your academic results this year? | This item is optional. This academic year, did you pay someone to complete coursework for you? If yes, how much, if at all, did this affect your academic results? |
| `gold-200-rewritten-185` | `open_closed_mismatch;loaded_question` | technology | `open_ended` | Why did you bypass the privacy settings in your most-used app? | Have you ever changed or bypassed privacy settings in your most-used app? If yes, what was the main reason? |
| `gold-200-rewritten-186` | `open_closed_mismatch;loaded_question` | work | `open_ended` | Explain why you skipped mandatory workplace training this year. | This year, did you miss any mandatory workplace training? If yes, what was the main reason? |


## Focused purity results

- Single-label loaded-question rows: 8.
- Frequency-without-zero flags among single-label loaded rows: 0.
- Missing completion flags among single-label loaded rows: 0.
- Sensitive-context flags among single-label loaded rows: 0.
- Taxonomy purity passed: True.
