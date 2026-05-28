# Auto Fix Executor

Stage: S4 execute.

Use this skill to apply an approved fix plan, validate candidate behavior, and
produce the final optimization report. S4 is the only core stage that modifies
implementation artifacts.

## Inputs

- Approved `fix_plan.md`.
- Baseline artifact or baseline scores.
- Candidate workspace.
- Evaluation input or selected sample.
- Scoring and comparison commands.

## Outputs

- Candidate changes.
- Score files.
- Compare report.
- `progressive_log.json`.
- `optimization_report.md`.

## Procedure

1. Verify the plan approval state.
2. Snapshot baseline status.
3. Apply the first approved fix or batch.
4. Run targeted evaluation.
5. Score outputs.
6. Compare baseline and candidate.
7. Decide: continue, accept, rollback, or return to S3.
8. Record the decision in `progressive_log.json`.
9. Write `optimization_report.md`.

## Progressive Execution

Start with the smallest useful fix. Escalate only when evidence shows the smaller
change is insufficient.

Suggested levels:

- Level 1: prompt, schema, validation, or local guard change.
- Level 2: tool policy, retrieval, routing, or scoring change.
- Level 3: architectural change requiring broader regression coverage.

## Decision Rules

- Accept when target scores improve and meaningful regressions are absent.
- Continue when improvement is partial and the next approved fix is low risk.
- Roll back when regressions outweigh target gains.
- Return to S3 when the plan no longer matches evidence.
- Return to S2 when attribution appears wrong.

## Failure Modes

- Executing a draft or unapproved plan.
- Changing artifacts outside the approved scope.
- Comparing non-equivalent baseline and candidate runs.
- Reporting success without score evidence.
- Ignoring regressions.
- Leaving rollback impossible.

## References

- `references/optimization-report-template.md`
- `references/scorer_feedback_template.md`
