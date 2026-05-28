# Auto Trace Prep

Stage: S1 prepare.

## Purpose

Prepare the evidence package that downstream analysis can consume without chat
history. S1 freezes selected eval rows, runner outputs, trace files, schema
notes, and review status in `analysis_manifest.json`.

## Inputs

- Evaluation input CSV or equivalent structured dataset.
- Runner output CSV, if execution already happened.
- Optional cleaned trace files.
- Optional case selection list.
- Expected behavior fields or a schema mapping.

## Outputs

- `analysis_manifest.json`.
- Cleaned trace files when traces are available.
- Preparation note for human review.

## Procedure

1. Inspect input schema.
2. Confirm case ID and expected-behavior fields.
3. Select target cases.
4. Match runner outputs and traces to selected cases.
5. Clean trace fields that may contain secrets or unnecessary raw payloads.
6. Write `analysis_manifest.json`.
7. Request human confirmation when scope, schema, or privacy is uncertain.

## Human Gate

The manifest is not ready for S2 until selected cases, expected behavior, trace
coverage, privacy status, and unresolved assumptions are reviewed. Set
`review_status` to `confirmed` only after this gate.

## Failure Modes

- Case IDs are missing or unstable.
- Expected behavior cannot be found.
- Trace files do not match selected cases.
- Data is not approved for the target repository.
- The runner output cannot be reproduced.

## Manifest Shape

```json
{
  "experiment_id": "example_experiment",
  "display_name": "Example Experiment",
  "schema": {},
  "selected_cases": [],
  "trace_files": [],
  "run_metadata": {},
  "review_status": "draft"
}
```
