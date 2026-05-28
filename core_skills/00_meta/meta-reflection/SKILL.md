# Meta Reflection

## Purpose

Run a lightweight quality check at a stage exit before the workflow moves
forward.

## Inputs

- Stage name: `S1`, `S2`, `S3`, or `S4`.
- Stage output artifact.
- Source evidence used by that stage.
- Known assumptions and unresolved questions.
- Optional reviewer notes.

## Outputs

- `reflection.md` or a reflection section inside the stage artifact.
- Recommendation: `proceed`, `revise_current_stage`,
  `return_to_previous_stage`, or `stop_for_human_review`.

## Procedure

1. Confirm the artifact can be reproduced from named files or commands.
2. Check that evidence, hypotheses, assumptions, and decisions are separate.
3. Verify that public-bound material excludes private data.
4. Confirm the next stage has the inputs it needs.
5. Choose one recommendation and name the required next action.

## Human Gate

Stop for human review when evidence is weak, privacy status is uncertain, the
next stage is missing required inputs, or the artifact claims success without
supporting data.

## Failure Modes

- The artifact is plausible but not evidence-backed.
- Private identifiers or real data appear in public-bound material.
- The next stage depends on hidden chat history.
- A decision is implied but not explicitly recorded.
