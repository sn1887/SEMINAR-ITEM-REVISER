## Completion note

Completed on 2026-08-21. Baseline compile produced a 24-page PDF before the
restructuring pass, but the original BibTeX run failed because of a multiline
citation key formatting issue. The revised report compiles cleanly with
`latexmk -pdf -interaction=nonstopmode -halt-on-error report.tex` and produces
an 18-page `report.pdf`.

## Phase 1 — Make the structural changes first

* [x] **1. Remove `Report Structure` from the Introduction.**
  Delete:

  ```latex
  \subsection{Report Structure}
  \label{subsec:report-structure}
  ```

  together with the paragraph explaining what each later section contains.


---

## Phase 2 — Create the appendix before moving anything

* [x] **6. Insert an appendix structure after the bibliography.**

  Use approximately this structure:

  ```latex
  % =========================================================
  % APPENDIX
  % =========================================================

  \appendix

  \section{Supplementary Benchmark Information}
  \label{app:benchmark}

  \section{Supplementary Prompt-Pack Information}
  \label{app:prompt-packs}

  \section{Supplementary Detection Results}
  \label{app:detection}

  \section{Supplementary Revision Results}
  \label{app:revision}

  \section{Supplementary Thinking-Mode Results}
  \label{app:thinking}

  \section{Exploratory Semantic Option Matching Metric}
  \label{app:som-f1}
  ```

* [x] **7. Do not rewrite any moved table yet.**
  Copy it exactly as it currently exists, including its original `\label{...}`. Keeping the same labels means existing `\ref{...}` references will continue to work.

---

## Phase 3 — Move supplementary benchmark material

* [x] **8. Move the benchmark topic table to Appendix A.**
  Move:

  ```latex
  \label{tab:benchmark-topics}
  ```

  into:

  ```latex
  \section{Supplementary Benchmark Information}
  ```

* [x] **9. Replace the removed table in the main text with one sentence.**
  Keep only the substantive result:

  > The benchmark spans 14 substantive domains, nine response formats, and three approximately balanced difficulty groups; detailed topic counts are reported in Appendix~\ref{app:benchmark}.

* [x] **10. Keep the benchmark-composition table in the main paper.**
  Do **not** move:

  ```latex
  \label{tab:benchmark-composition}
  ```

  The 200 / 40 / 115 / 45 composition is fundamental to understanding the experiment.

* [x] **11. Keep the taxonomy table in the main paper.**
  Do **not** move:

  ```latex
  \label{tab:taxonomy}
  ```

  Readers need the five families and 16-label taxonomy before they can understand the results.

* [x] **12. Compile.**

---

## Phase 4 — Move supplementary prompt information

* [x] **13. Move the P2 demonstration-distribution table to Appendix B.**
  Move:

  ```latex
  \label{tab:p2-examples}
  ```

  into:

  ```latex
  \section{Supplementary Prompt-Pack Information}
  ```

* [x] **14. In the main Methodology, replace the table with one compact sentence.**
  For example:

  > P2 contains 37 fixed, role-specific demonstrations spanning all five specialist families; the full role-wise distribution is reported in Appendix~\ref{app:prompt-packs}.

* [x] **15. Keep the important qualification in the main paper:**

  ```latex
  P2 is family-complete, but not taxonomy-complete.
  ```

  This becomes important when interpreting the per-label results later.

* [x] **16. Compile.**

---

## Phase 5 — Move the Related Work comparison table

* [x] **17. Move the entire related-work comparison table out of the main text.**
  Move:

  ```latex
  \label{tab:related-work-comparison}
  ```

  You can place it in a new appendix subsection such as:

  ```latex
  \subsection{Detailed Comparison with Prior Work}
  ```

  This could either be under Appendix A or, if you prefer cleaner organization, its own appendix:

  ```latex
  \section{Detailed Related-Work Comparison}
  ```

* [x] **18. Keep only one short positioning paragraph in the main Related Work section.**
  You do not need both the long comparison table and several paragraphs saying what distinguishes your study.

* [x] **19. Compile.**

---

## Phase 6 — Move detailed detection diagnostics

This is where the main Results section will become much cleaner.

* [x] **20. Keep the main overall detection table.**
  Keep:

  ```latex
  \label{tab:overall-detection}
  ```

  This is one of your core result tables.

* [x] **21. Move the P0 cross-model family table to Appendix C.**
  Move:

  ```latex
  \label{tab:p0-cross-model-families}
  ```

* [x] **22. Keep the cross-model conclusion in the main text, but shorten it.**
  The main paper only needs to establish that:

  * Qwen was strongest;
  * Gemma was intermediate;
  * Mistral was weakest;
  * orchestration could produce deceptively low clean FPR through under-detection.

  The complete family breakdown can remain in the appendix.

* [x] **23. Move the Qwen TP/FP/FN diagnostic table to Appendix C.**
  Move:

  ```latex
  \label{tab:qwen-detection-counts}
  ```

  The main `overall-detection` table already reports precision, recall, F1, exact match, and clean FPR.

* [x] **24. Keep the Qwen family-level table in the main paper.**
  Keep:

  ```latex
  \label{tab:qwen-family-f1}
  ```

  This table is important because it demonstrates where P1 and P2 actually helped.

* [x] **25. Move the large 16-label F1 table to Appendix C.**
  Move:

  ```latex
  \label{tab:qwen-label-f1}
  ```

  This should definitely not consume main-paper space.

* [x] **26. Keep only the most important per-label observations in the main text.**
  Specifically retain:

  * strong P2 gains for leading/loaded questions;
  * improvements in response-option/scale defects;
  * persistent failures for `recall_error`, `non_exclusive_options`, and `unbalanced_scale`;
  * the implication that family-complete examples do not guarantee taxonomy-complete performance.

* [x] **27. Compile and check that every appendix table reference still works.**

---

## Phase 7 — Preserve the multi-label result in the main paper

* [x] **28. Keep the prediction-cardinality table in the main text.**
  Do **not** move:

  ```latex
  \label{tab:cardinality-results}
  ```

* [x] **29. Keep the associated multi-label discussion.**
  This is one of the most important findings in the whole paper:

  * baseline frequently predicts multiple labels;
  * orchestration predicts only zero or one;
  * no Qwen orchestrated condition achieves a multi-label exact match;
  * fallback therefore cannot fix the problem because the router never supplies the complete issue set.

  This deserves main-paper space.

* [x] **30. Do not overcompress this subsection merely to save pages.**

---

## Phase 8 — Move detailed revision diagnostics

* [x] **31. Keep the end-to-end revision table in the main text.**
  Keep:

  ```latex
  \label{tab:e2e-revision-results}
  ```

  This is the principal revision result.

* [x] **32. Move the complete oracle-revision table to Appendix D.**
  Move:

  ```latex
  \label{tab:oracle-revision-results}
  ```

* [x] **33. Keep a short oracle paragraph in the main paper.**
  The important finding is:

  * oracle revision was not a strict upper bound;
  * correct labels without item-specific evidence could still cause the conservative revisers to reject a repair;
  * exact-full revision remained very low.

* [x] **34. Avoid repeating the exact-option limitation multiple times.**
  Explain once that exact matching is intentionally strict and that one reference revision cannot cover every semantically valid alternative.

* [x] **35. Compile.**

---

## Phase 9 — Compress the thinking-mode material

* [x] **36. Move the detailed thinking-completion table to Appendix E.**
  Move:

  ```latex
  \label{tab:thinking-completion}
  ```

* [x] **37. Keep the matched thinking-vs-non-thinking detection table in the main paper.**
  Keep:

  ```latex
  \label{tab:thinking-matched-detection}
  ```

  It gives the cleanest answer to RQ5.

* [x] **38. Move the one-row conditional revision table to Appendix E or remove the table formatting entirely.**
  This is:

  ```latex
  \label{tab:thinking-conditional-revision}
  ```

  Since it contains only one row, it does not need to occupy main-paper table space.

* [x] **39. In the main text, reduce thinking mode to three points:**

  * reasoning improved performance conditional on successful outputs;
  * completion reliability was poor because of token exhaustion;
  * successful outputs were heavily biased away from multi-label cases, preventing a full-benchmark conclusion.

* [x] **40. Compile.**

---

## Phase 10 — Move SOM-F1 to the appendix

* [x] **41. Shorten `Future Work` in the main paper.**
  Remove the SOM-F1 equations and detailed implementation proposal from the main section.

* [x] **42. Leave only a short pointer in Future Work.**
  For example:

  > A further direction concerns semantic evaluation of response-option revisions. Exact matching penalizes semantically equivalent alternatives, motivating an exploratory semantic option-matching measure. Appendix~\ref{app:som-f1} outlines a possible SOM-F1 formulation and the independent validation required before such a metric could be used in evaluation.

* [x] **43. Move the complete SOM-F1 proposal into Appendix F.**
  Preserve:

  * motivation;
  * definitions of predicted and gold option sets;
  * semantic pair scoring;
  * Hungarian matching;
  * semantic precision;
  * semantic recall;
  * SOM-F1 equation;
  * bidirectional entailment idea;
  * contradiction handling;
  * proposed human-labelled validation set;
  * held-out validation requirement.

* [x] **44. Explicitly call the metric `exploratory` or `proposed`.**
  It was not part of the experiments reported in the paper, and the appendix should make that distinction unambiguous.

* [x] **45. Compile.**

---

## Phase 11 — Remove duplicated Results material

* [x] **46. Delete the entire subsection:**

  ```latex
  \subsection{Answers to the Research Questions}
  \label{subsec:rq-answers}
  ```

  including the five RQ paragraphs.

* [x] **47. Do not move this subsection to the appendix.**
  It is repetition rather than supplementary evidence.

* [x] **48. Instead, answer the five RQs naturally in the Results discussion and summarize them once in the Conclusion.**

* [x] **49. Compile.**

---

