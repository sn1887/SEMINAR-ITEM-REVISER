# Professor Feedback Resolution — v4

This document maps every comment to a concrete dataset change. “Item153 and following” is interpreted as Items153–160 because those eight rows form the complete `too_many_scale_points` block with unlabeled numeric points.

## Design decision

The additional labels are retained even though they break the previous exact label balance. Removing valid labels merely to preserve equal counts would make the gold annotations less defensible.

### Item003 — `gold-200-rewritten-003`

- **Issue:** Mixed count and rate categories.
- **Action:** Use count categories consistently; remove the mixed count/rate endpoint “Daily”.
- **Labels:** `clean` → `clean`
- **Question:** In the past 7 days, how many times did you use public transport for trips within your city?
- **Options:** 0 times; 1 time; 2-3 times; 4-6 times; 7 or more times
- **Expected revision:** In the past 7 days, how many times did you use public transport for trips within your city?
### Item007 — `gold-200-rewritten-007`

- **Issue:** Vague quantification; ask for a count or rate.
- **Action:** Replace vague verbal frequency categories with an explicit opportunity-based rate and a fixed reference period.
- **Labels:** `clean` → `clean`
- **Question:** In the past 7 days, when a light or device in your home was not being used, how often did someone in your household turn it off?
- **Options:** Never; Less than half of the time; About half of the time; More than half of the time; Every time; Not applicable
- **Expected revision:** In the past 7 days, when a light or device in your home was not being used, how often did someone in your household turn it off?
### Item008 — `gold-200-rewritten-008`

- **Issue:** Vague quantification; ask for a count or rate.
- **Action:** Replace vague frequency categories with an explicit rate over a fixed reference period and add non-applicable paths.
- **Labels:** `clean` → `clean`
- **Question:** During the past 7 days, on the days when you worked or studied and needed a short break, how often were you able to take one?
- **Options:** Never; Less than half of the time; About half of the time; More than half of the time; Every time; I did not work or study; I did not need a break
- **Expected revision:** During the past 7 days, on the days when you worked or studied and needed a short break, how often were you able to take one?
### Item013 — `gold-200-rewritten-013`

- **Issue:** Mixed count and rate categories.
- **Action:** Use count categories consistently; remove the mixed count/rate endpoint “Daily”.
- **Labels:** `clean` → `clean`
- **Question:** In the past 7 days, how many times did you watch local news videos online?
- **Options:** 0 times; 1 time; 2-3 times; 4-6 times; 7 or more times
- **Expected revision:** In the past 7 days, how many times did you watch local news videos online?
### Item027 — `gold-200-rewritten-027`

- **Issue:** Vague quantification; ask for a count or rate.
- **Action:** Ask for a defined proportion rather than using vague frequency words.
- **Labels:** `clean` → `clean`
- **Question:** For assignments submitted this semester, for what proportion did you receive feedback before the next related deadline?
- **Options:** None; Less than half; About half; More than half; All; No assignments had a related later deadline; Not applicable
- **Expected revision:** For assignments submitted this semester, for what proportion did you receive feedback before the next related deadline?
### Item040 — `gold-200-rewritten-040`

- **Issue:** Mixed count and rate categories.
- **Action:** Use count categories consistently rather than mixing event counts with “Monthly or more often”.
- **Labels:** `clean` → `clean`
- **Question:** Some people prefer not to answer questions about gambling. During the last 12 months, how many times did you gamble with money?
- **Options:** 0 times; 1 time; 2-3 times; 4-11 times; 12 or more times; Prefer not to answer
- **Expected revision:** Some people prefer not to answer questions about gambling. During the last 12 months, how many times did you gamble with money?
### Item090 — `gold-200-rewritten-090`

- **Issue:** Also warrants vague_ambiguous.
- **Action:** Add vague_ambiguous because the original reference period, target event, or frequency task is underspecified; ensure the expected revision addresses it.
- **Labels:** `social_desirability` → `social_desirability, vague_ambiguous`
- **Question:** In a typical day, how often do you make the healthy choice to eat fruit?
- **Options:** Rarely; Usually; Always
- **Expected revision:** In the past 7 days, on how many days did you eat at least one portion of fruit?
### Item091 — `gold-200-rewritten-091`

- **Issue:** Also warrants vague_ambiguous.
- **Action:** Add vague_ambiguous because the original reference period, target event, or frequency task is underspecified; ensure the expected revision addresses it.
- **Labels:** `social_desirability` → `social_desirability, vague_ambiguous`
- **Question:** Responsible citizens vote in local elections. Did you vote in the most recent local election?
- **Options:** Yes; No
- **Expected revision:** In the municipal election held on 15 March 2026, did you vote?
### Item092 — `gold-200-rewritten-092`

- **Issue:** Also warrants vague_ambiguous.
- **Action:** Add vague_ambiguous because the original reference period, target event, or frequency task is underspecified; ensure the expected revision addresses it.
- **Labels:** `social_desirability` → `social_desirability, vague_ambiguous`
- **Question:** At work, how often do you honestly report mistakes instead of hiding them?
- **Options:** Never; Sometimes; Always; Not applicable
- **Expected revision:** In the last 3 months, how often did you report a work mistake to the person responsible for handling it?
### Item093 — `gold-200-rewritten-093`

- **Issue:** Also warrants vague_ambiguous.
- **Action:** Add vague_ambiguous because the original reference period, target event, or frequency task is underspecified; ensure the expected revision addresses it.
- **Labels:** `social_desirability` → `social_desirability, vague_ambiguous`
- **Question:** Before class, how often do you come prepared like a serious student?
- **Options:** Never; Sometimes; Always
- **Expected revision:** During the last 2 weeks of classes, how often did you complete the assigned preparation before class?
### Item100 — `gold-200-rewritten-100`

- **Issue:** Also warrants agree_disagree_scale.
- **Action:** Add agree_disagree_scale because agreement categories are used to measure perceived clarity.
- **Labels:** `negative_wording` → `negative_wording, agree_disagree_scale`
- **Question:** To what extent do you disagree that exam instructions were not unclear?
- **Options:** Strongly disagree; Somewhat disagree; Neither agree nor disagree; Somewhat agree; Strongly agree
- **Expected revision:** How clear or unclear were the exam instructions?
### Item110 — `gold-200-rewritten-110`

- **Issue:** The open/closed mismatch is not sufficiently clear.
- **Action:** Strengthen open_closed_mismatch by pairing an explicit request for an open explanation with closed-only response options.
- **Labels:** `open_closed_mismatch` → `open_closed_mismatch`
- **Question:** Which privacy improvement would you most like app developers to make? Please explain your answer in your own words.
- **Options:** Clearer permission requests; Easier deletion of data; Less third-party sharing; More control over notifications; Other
- **Expected revision:** Which privacy improvement would you most like app developers to make?
### Item153 — `gold-200-rewritten-153`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** Using the 0-to-20 scale, indicate your support or opposition to participatory budgeting in your municipality.
- **Options:** 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20
- **Expected revision:** To what extent do you support or oppose participatory budgeting in your municipality?
### Item154 — `gold-200-rewritten-154`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** On a 0-to-100 scale, rate your satisfaction with pharmacy opening hours in your area.
- **Options:** 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31; 32; 33; 34; 35; 36; 37; 38; 39; 40; 41; 42; 43; 44; 45; 46; 47; 48; 49; 50; 51; 52; 53; 54; 55; 56; 57; 58; 59; 60; 61; 62; 63; 64; 65; 66; 67; 68; 69; 70; 71; 72; 73; 74; 75; 76; 77; 78; 79; 80; 81; 82; 83; 84; 85; 86; 87; 88; 89; 90; 91; 92; 93; 94; 95; 96; 97; 98; 99; 100
- **Expected revision:** How satisfied or dissatisfied are you with pharmacy opening hours in your area?
### Item155 — `gold-200-rewritten-155`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** Rate your concern about microplastics in local waterways on a 0-to-30 scale.
- **Options:** 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30
- **Expected revision:** How concerned are you about microplastics in local waterways?
### Item156 — `gold-200-rewritten-156`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** How important are digital literacy classes in secondary schools?
- **Options:** 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15
- **Expected revision:** How important or unimportant are digital literacy classes in secondary schools?
### Item157 — `gold-200-rewritten-157`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** Choose a number from 0 to 25 to show your satisfaction with bicycle parking near train stations.
- **Options:** 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25
- **Expected revision:** How satisfied or dissatisfied are you with bicycle parking near train stations?
### Item158 — `gold-200-rewritten-158`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** How fair is the allocation of shifts in your workplace?
- **Options:** 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31; 32; 33; 34; 35; 36; 37; 38; 39; 40; 41; 42; 43; 44; 45; 46; 47; 48; 49; 50
- **Expected revision:** How fair or unfair is the allocation of shifts in your workplace?
### Item159 — `gold-200-rewritten-159`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** Use the 0-to-20 scale to show your trust in cloud storage providers to protect your files.
- **Options:** 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20
- **Expected revision:** How much do you trust or distrust cloud storage providers to protect your files?
### Item160 — `gold-200-rewritten-160`

- **Issue:** Also warrants missing_scale_labels.
- **Action:** Add missing_scale_labels because the high-resolution numeric options do not define endpoint direction or midpoint meaning.
- **Labels:** `too_many_scale_points` → `too_many_scale_points, missing_scale_labels`
- **Question:** For this semester’s exam schedule, choose a number from 0 to 40 to show your satisfaction.
- **Options:** 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31; 32; 33; 34; 35; 36; 37; 38; 39; 40
- **Expected revision:** How satisfied or dissatisfied are you with the scheduling of exams this semester?
### Item191 — `gold-200-rewritten-191`

- **Issue:** Also warrants negative_wording because of “fail”.
- **Action:** Add negative_wording because “fail to report” frames the behavior negatively and complicates yes/no interpretation; revise to neutral categorical statements.
- **Labels:** `sensitive_topic_direct, social_desirability` → `sensitive_topic_direct, social_desirability, negative_wording`
- **Question:** Honest people report all taxable income. Did you fail to report any taxable income last year?
- **Options:** Yes; No
- **Expected revision:** People’s tax filing situations differ, and you may skip this question. For your most recent tax filing, which statement best describes the taxable income reported?

