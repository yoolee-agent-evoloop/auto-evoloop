# Meta Reflection

Use this skill at any stage exit to decide whether the current evidence is strong
enough to move forward. It is a lightweight governance step, not a substitute for
S1-S4.

## Trigger

Run after:

- S1 produces a manifest,
- S2 produces reports or feedback,
- S3 produces a fix plan,
- S4 produces an optimization report,
- a reviewer identifies uncertainty that may affect the next stage.

## Inputs

- Stage name: `S1`, `S2`, `S3`, or `S4`.
- Stage output artifact.
- Source evidence used by that stage.
- Known assumptions and unresolved questions.
- Optional reviewer notes.

## Outputs

- `reflection.md` or an embedded reflection section in the stage artifact.
- A recommendation: `proceed`, `revise_current_stage`, `return_to_previous_stage`,
  or `stop_for_human_review`.

## Review Questions

1. Is the stage output reproducible from named files or commands?
2. Does the artifact separate evidence from hypothesis?
3. Are private or non-public materials excluded or explicitly approved?
4. Are assumptions visible enough for a reviewer to challenge?
5. Does the next stage have the exact inputs it needs?
6. Is a human decision required before moving on?

## Stage Modules

- `stages/S1.md`: manifest and evidence readiness.
- `stages/S2.md`: attribution quality.
- `stages/S3.md`: plan quality and approval.
- `stages/S4.md`: validation evidence and release readiness.

## Failure Modes

- The artifact is plausible but not tied to evidence.
- The artifact hides uncertainty as confident language.
- The next stage requires private context that is not included.
- The stage output includes real data or private identifiers.
- A plan or report claims success without baseline/candidate evidence.
