# Auto Case Summary

Stage: S2 summary, deprecated.

This skill is retained as a migration reference for teams that still aggregate
many case reports before planning. New workflows should pass structured
`feedback.json` from `auto-single-case-analyzer` directly into S3.

## Inputs

- Multiple `case_report.md` files.
- Multiple feedback JSON objects.
- Experiment objective.

## Outputs

- `case_summary.md`.
- Optional merged `feedback.json`.

## Procedure

1. Group findings by failure mode.
2. Identify repeated evidence patterns.
3. Separate high-confidence findings from weak hypotheses.
4. Highlight fixes that would address multiple cases.
5. Preserve minority findings that may represent regressions or edge cases.

## Deprecation Note

Do not use this skill to hide case-level uncertainty. If cases disagree, keep the
conflict visible for S3.
