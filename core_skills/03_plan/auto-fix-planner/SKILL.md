# Auto Fix Planner

Stage: S3 plan.

Use this skill to convert analyzed failures into an approved, reviewable fix plan.
The planner should not edit implementation files. It produces the contract that
S4 will execute.

## Inputs

- Confirmed S2 `feedback.json`.
- Relevant `case_report.md` files.
- Current source, prompt, tool, or configuration context.
- Baseline score summary, when available.
- Experiment objective.

## Outputs

- `fix_plan.md`.
- Optional `fix_plan.json` if downstream tooling needs structured input.

## Procedure

1. Group S2 findings by failure mode and repair direction.
2. Remove fixes that are unsupported by evidence.
3. Split broad ideas into focused fix items.
4. Order fixes from lowest risk to highest risk.
5. Define validation commands and success criteria.
6. Add rollback notes.
7. Request human approval before S4.

## Fix Item Contract

Each fix should include:

- `fix_id`
- evidence links
- target artifact
- intended behavior change
- risk level
- validation scope
- rollback note

## Plan Decisions

Use one of:

- `approved`: S4 may execute.
- `revise`: planner must update the plan.
- `needs_more_analysis`: return to S2.
- `rejected`: stop this round.

## Human Gate

The plan is not executable until approval is explicit in the file. Approval must
name the reviewer, date, and accepted validation scope.

## Failure Modes

- Fixes are not tied to evidence.
- Multiple unrelated changes are bundled into one fix.
- Validation cannot detect the intended improvement.
- Rollback is not possible.
- The plan changes private or production resources from a public example.

## References

- `references/attribution-framework.md`
- `references/fix-plan-templates.md`
- `references/repair-principles-v1.6.0.md`
