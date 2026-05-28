# Concepts

Auto-evoloop uses a four-layer improvement model. The same terminology is used
in docs, artifacts, logs, and skill contracts.

| Layer | Term | Definition | Typical path |
| --- | --- | --- | --- |
| L1 | Experiment | One improvement cycle around an evaluation dataset and a goal. | `experiments/<experiment_id>/` |
| L2 | Round | One approved fix plan and one execution attempt. | `rounds/round_N/` |
| L3 | Batch | A group of fixes applied and evaluated together inside a round. | `progressive_log.json[iterations]` |
| L4 | Fix | One focused behavior, prompt, tool, or configuration change. | `fix_plan.md` item |

## Naming Rules

- `evoloop` is the project name, not a workflow layer.
- `experiment_id` is stable and path-safe.
- `display_name` is human-facing and may be localized or changed.
- A new approved plan starts a new round.
- If execution needs to return to planning, start `round_{N+1}` instead of
  rewriting the previous round.

## Core Artifacts

| Artifact | Produced by | Consumed by | Purpose |
| --- | --- | --- | --- |
| `analysis_manifest.json` | S1 prepare | S2 analyze | Freezes selected cases, trace paths, schema, and scope. |
| `case_report.md` | S2 analyze | Human reviewers, S3 planner | Explains expected behavior, observed behavior, and root cause. |
| `feedback.json` | S2 analyze | S3 planner | Machine-readable case findings and repair hints. |
| `fix_plan.md` | S3 plan | S4 execute | Approved fix set, risk notes, validation plan, and rollback notes. |
| `progressive_log.json` | S4 execute | S4 decisions, final report | Records batches, scores, regressions, and decisions. |
| `optimization_report.md` | S4 execute | Humans, release notes | Summarizes changes, validation evidence, residual risk, and next steps. |

## Decision Gates

Auto-evoloop keeps human review inside each stage rather than as a separate
workflow node:

- S1 gate: confirm case selection, schema, and analysis scope.
- S2 gate: confirm attribution quality and whether more evidence is needed.
- S3 gate: approve, revise, or reject the fix plan.
- S4 gate: accept, continue, rollback, or return to planning.
