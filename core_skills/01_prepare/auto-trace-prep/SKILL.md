# Auto Trace Prep

Stage: S1 prepare.

Use this skill to prepare the evidence package that downstream analysis can
consume without chat history. It freezes selected eval rows, runner outputs,
trace files, schema notes, and review status in `analysis_manifest.json`.

## Inputs

- Evaluation input CSV or equivalent structured dataset.
- Runner output CSV, if the agent has already been executed.
- Optional trace files.
- Optional case selection list.
- Expected behavior fields or a mapping that explains where expectations live.

## Outputs

- `analysis_manifest.json`.
- Cleaned trace files, when trace input exists.
- A short preparation note for human review.

## Required Manifest Fields

```json
{
  "experiment_id": "example_experiment",
  "display_name": "Example Experiment",
  "schema": {
    "case_id": "case_id",
    "input": "input",
    "expected": "expected",
    "observed": "observed"
  },
  "selected_cases": [],
  "trace_files": [],
  "run_metadata": {},
  "review_status": "draft"
}
```

## Procedure

1. Inspect the input schema.
2. Confirm the case identifier and expected-behavior columns.
3. Select the target cases.
4. Match runner outputs and traces to selected cases.
5. Clean trace fields that may contain secrets or unnecessary raw payloads.
6. Write `analysis_manifest.json`.
7. Ask for human confirmation when scope, schema, or privacy is uncertain.

## Human Gate

The manifest is not ready for S2 until a human or maintainer confirms:

- selected cases are correct,
- expected behavior is available,
- private data is excluded,
- trace coverage is sufficient,
- unresolved assumptions are documented.

Set `review_status` to `confirmed` only after this gate.

## Failure Modes

- Case IDs are missing or unstable.
- Expected behavior cannot be found.
- Trace files do not match selected cases.
- The dataset contains real or private data that is not approved for the target
  repository.
- The runner output cannot be reproduced.

## References

- `references/environment-setup.md`
- `scripts/traces_fetch.py`
