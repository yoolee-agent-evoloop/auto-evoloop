# Auto Single Case Analyzer

Stage: S2 analyze.

## Purpose

Analyze one failing or suspicious case at a time. S2 separates evidence,
interpretation, and repair hints so S3 can plan without re-reading every trace.

## Inputs

- Confirmed `analysis_manifest.json`.
- One selected case ID.
- Cleaned trace or runner output for that case.
- Expected behavior.
- Optional baseline/candidate comparison.

## Outputs

- `case_report.md`.
- `feedback.json`.

## Procedure

1. Restate case scope and expected behavior.
2. Summarize observed behavior.
3. Extract evidence from trace, output, and eval fields.
4. Identify the failure mode or mark `needs_more_evidence`.
5. Explain alternative hypotheses when they matter.
6. Produce the smallest useful repair hint.
7. Write human-readable and structured outputs.

## Human Gate

A reviewer should confirm that evidence supports the finding, uncertainty is
visible, repair hints are not broader than evidence, and no private data is
included.

## Failure Modes

- The report invents evidence.
- The finding is too broad to plan a fix.
- The repair hint changes unrelated behavior.
- The analysis depends on private context not present in artifacts.

## Feedback Shape

```json
{
  "case_id": "case_001",
  "finding": "short finding",
  "failure_mode": "instruction_following",
  "evidence": [],
  "alternative_hypotheses": [],
  "repair_hint": "smallest useful repair",
  "confidence": "medium"
}
```
