# Auto Fix Executor

Stage: S4 execute.

## Purpose

Apply an approved fix plan, validate candidate behavior, and produce the final
optimization report. S4 is the only core stage that modifies implementation
artifacts.

## Inputs

- Approved `fix_plan.md`.
- `analysis_manifest.json`.
- Reviewed `feedback.json`.
- Baseline artifact or baseline scores.
- Agent source files declared by the manifest.
- Eval, scorer, and compare adapters.

## Outputs

- Candidate changes.
- Eval and score outputs.
- `progressive_log.json`.
- `optimization_report.md`.
- Diffs or change summaries.

## Procedure

1. Verify the plan is approved.
2. Snapshot baseline status.
3. Apply the next approved fix or batch.
4. Run eval through the configured adapter.
5. Score and compare baseline vs candidate.
6. Record D1 decision: `COMMIT` or `ROLLBACK`.
7. Record D2 decision: `CONTINUE` or `EXIT`.
8. Write `progressive_log.json` after every iteration.
9. Write `optimization_report.md`.

## Human Gate

Humans accept, continue, roll back, or return to planning based on score delta,
regressions, execution observations, and residual risk.

## Failure Modes

- Executing a draft or unapproved plan.
- Changing artifacts outside approved scope.
- Comparing non-equivalent baseline and candidate runs.
- Treating fast verification as final release evidence.
- Ignoring regressions.
- Changing fix intent instead of implementation details.

## Execution Contract

- Target and guardrail evals must be tracked separately.
- Sample selection should remain fixed within a round.
- Release-level validation is required before final acceptance.
- `progressive_log.json` is the recovery and decision source of truth.
