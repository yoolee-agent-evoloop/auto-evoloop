# Auto Fix Planner

Stage: S3 plan.

## Purpose

Convert reviewed S2 findings into an approved, reviewable fix plan. The planner
does not edit implementation files. It creates the contract that S4 executes.

## Inputs

- Confirmed `analysis_manifest.json`.
- Reviewed `feedback.json`.
- Relevant case reports or summaries.
- Agent source files declared by the manifest.
- Baseline score summary, when available.
- Experiment objective.

## Outputs

- `fix_plan.md`.
- Optional structured fix plan JSON for tooling.
- External issue list for findings that should not enter automatic fixing.

## Procedure

1. Read only cases that are accepted for repair.
2. Separate agent-fixable findings from evaluator, data, or environment issues.
3. Map each fix to source cases, root causes, evidence, and causal edges.
4. Split broad ideas into focused fix items.
5. Order fixes by dependency and risk.
6. Define validation, expected tradeoffs, constraints, and rollback.
7. Request human approval before S4.

## Human Gate

The plan is executable only when approval is explicit. Approval must name the
reviewer, decision, accepted validation scope, and any excluded risks.

## Failure Modes

- Fixes are not tied to S2 evidence.
- External issues are planned as agent fixes.
- Multiple unrelated changes are bundled into one fix.
- Validation cannot detect the intended improvement.
- The plan assumes a private source layout or hidden runtime.

## Fix Item Contract

Each fix should include:

- `fix_id`
- `source_cases`
- `source_root_causes`
- `derivation_note`
- `target`
- `target_layer`
- `fix_strategy`
- `constraints`
- `expected_tradeoffs`
- `validation`
- `rollback`

Executor may refine implementation details, but must not change the fix intent.
