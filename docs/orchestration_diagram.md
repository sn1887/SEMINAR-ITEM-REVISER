# Item Reviser Orchestration Diagram

This diagram sketches the proposed LLM-agent orchestration for the item-reviser pipeline.
The core idea is to avoid a brittle single-label router and instead use a multi-label
quality check, a revision plan, targeted revision, and verification.

```mermaid
flowchart TD
    A[Survey Item] --> B[Quality Checker Agent]

    B --> C{Issue Decision}
    C -->|No issue / low risk| D[Leave Unchanged Candidate]
    C -->|One or more issues| E[Revision Planner Agent]

    E --> F[Revision Plan]
    F --> G{Needed Repair Families}

    G -->|Wording| H[Wording Revision Skill]
    G -->|Scale / Options| I[Scale Revision Skill]
    G -->|Sensitive / Social Desirability| J[Sensitivity Revision Skill]
    G -->|Construct Risk| K[Construct Preservation Check]

    H --> L[Final Item Reviser Agent]
    I --> L
    J --> L
    K --> L
    D --> M[Revision Verifier Agent]
    L --> M

    M --> N{Verifier Decision}
    N -->|Pass| O[Final Output]
    N -->|Fail, retry budget remains| E
    N -->|Fail, retry budget exhausted| P[Manual Review Flag]

    O --> Q[Evaluation Record]
    P --> Q

    subgraph CheckerOutput[Quality Checker Output]
        B1[Multi-label categories]
        B2[Severity]
        B3[Confidence]
        B4[Evidence]
        B5[No-issue decision]
    end

    subgraph VerifierChecks[Verifier Checks]
        M1[Original issue fixed?]
        M2[Target concept preserved?]
        M3[No new taxonomy issue?]
        M4[Clean item left unchanged?]
    end

    B -. produces .-> CheckerOutput
    M -. checks .-> VerifierChecks
```

## Agent Responsibility Matrix

| Stage | Main Job | Output | Main Failure To Guard Against |
|---|---|---|---|
| Quality Checker | Detect all relevant taxonomy issues, or decide no issue | Multi-label issue list with evidence and confidence | Missing multi-error items or over-flagging clean items |
| Revision Planner | Convert detected issues into repair actions | Ordered revision plan | Jumping directly to a bad rewrite without preserving intent |
| Revision Skills | Apply targeted fixes by issue family | Candidate repair instructions or partial rewrite | Treating every taxonomy category as a separate agent |
| Final Reviser | Produce one coherent revised item | Revised question, response options, notes, changed flag | Patchwork revisions that conflict with each other |
| Verifier | Audit the revised item against original and taxonomy | Pass, retry, or manual review | Accepting a fluent but concept-drifting revision |

## Minimal MVP Version

```mermaid
flowchart LR
    A[Survey Item] --> B[Quality Checker]
    B --> C{Needs Revision?}
    C -->|No| D[Verifier]
    C -->|Yes| E[Revision Planner]
    E --> F[Item Reviser]
    F --> D
    D -->|Pass| G[Final Output]
    D -->|One Retry| E
    D -->|Still Fails| H[Manual Review]
```

## Suggested Internal State

```json
{
  "detected_issues": [
    {
      "category": "leading_question",
      "family": "wording",
      "severity": "high",
      "confidence": 0.86,
      "evidence": "Don't you agree",
      "repair_strategy": "neutralize wording"
    }
  ],
  "decision": {
    "needs_revision": true,
    "reason": "High-confidence wording issue detected."
  },
  "revision_plan": [
    "Rewrite as a neutral support/oppose question.",
    "Use balanced item-specific response options."
  ],
  "verifier": {
    "status": "pass",
    "remaining_retry_budget": 1
  }
}
```
