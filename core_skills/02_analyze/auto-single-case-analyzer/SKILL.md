# Auto Single Case Analyzer

Stage: S2 analyze.

Use this skill to analyze one failing or suspicious case at a time. The output
must separate evidence, interpretation, and repair hints so that S3 can plan
fixes without re-reading every trace.

## Inputs

- Confirmed `analysis_manifest.json`.
- One selected case ID.
- Cleaned trace or runner output for that case.
- Expected behavior.
- Optional prior baseline/candidate comparison.

## Outputs

- `case_report.md`.
- `feedback.json`.

## Procedure

1. Restate the case scope and expected behavior.
2. Summarize observed behavior.
3. Extract evidence from trace, output, and eval fields.
4. Identify the failure mode or mark `needs_more_evidence`.
5. Explain why alternative hypotheses are weaker.
6. Produce a focused repair hint.
7. Write the human report and structured feedback.

## Failure Mode Vocabulary

Use these categories unless a project defines a compatible extension:

- `instruction_following`
- `retrieval_or_context`
- `tool_use`
- `reasoning`
- `format_or_schema`
- `safety_or_policy`
- `evaluation_or_label`
- `needs_more_evidence`

## Feedback JSON Shape

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

## Human Gate

A reviewer should confirm:

- evidence supports the finding,
- uncertainty is visible,
- the repair hint is not broader than the evidence,
- no real/private data is included.

## Failure Modes

- The report invents evidence.
- The finding is too broad to plan a fix.
- The repair hint changes unrelated behavior.
- The analysis depends on private context not present in artifacts.

## References

- `references/attribution-framework.md`
- `references/repair-principles-v1.6.0.md`
- `references/report-templates.md`
- `references/subagent-prompt-template.md`
- `scripts/generate_feedback_viewer.py`
