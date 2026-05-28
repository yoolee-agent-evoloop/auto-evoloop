# Auto-evoloop Core Design

This document is the source of truth for the public Auto-evoloop workflow. It is
adapted for open source use: business projects, private endpoints, real traces,
internal prompts, and deployment details are intentionally excluded.

## 0. Terminology

Auto-evoloop is organized around four layers:

| Layer | Term | Definition | Boundary |
| --- | --- | --- | --- |
| L1 | Experiment | A full improvement cycle around one dataset and one goal. | Starts when the eval input and objective are frozen. Ends when the outcome is accepted or abandoned. |
| L2 | Round | One approved plan and one execution attempt. | Starts from an approved `fix_plan.md`. Ends with an `optimization_report.md`. |
| L3 | Batch | A group of fixes applied and evaluated together. | One apply/eval/decision unit inside S4. |
| L4 | Fix | One focused behavior, prompt, tool, or configuration change. | The smallest planned change that can be reviewed and rolled back. |

`evoloop` is the project name, not a workflow layer. Use the four terms above in
paths, reports, logs, and review comments.

## 1. Design Goals

1. Make agent improvement reproducible through file-based artifacts.
2. Separate evidence preparation, failure analysis, fix planning, and execution.
3. Keep human-in-the-loop decisions explicit and auditable.
4. Support gradual optimization: small changes first, broader changes only when
   evidence justifies them.
5. Keep public examples synthetic and safe to run offline.

## 2. Idempotency

Each stage is structurally idempotent:

- Inputs are files or explicit command arguments.
- Outputs are written to known artifact paths.
- Re-running a stage with the same inputs should preserve the same artifact
  structure.
- LLM text, external agent behavior, and runtime scores may vary. The workflow
  records enough metadata for humans to understand that variation.

## 3. Stage Overview

| Stage | Skill | Inputs | Outputs | Human gate |
| --- | --- | --- | --- | --- |
| S1 | `auto-trace-prep` | eval input, runner output, optional traces | `analysis_manifest.json`, cleaned traces | Confirm selected cases and schema. |
| S2 | `auto-single-case-analyzer` | manifest, traces, expected behavior | `case_report.md`, `feedback.json` | Confirm attribution quality. |
| S3 | `auto-fix-planner` | feedback, reports, source/context | `fix_plan.md` | Approve or revise the plan. |
| S4 | `auto-fix-executor` | approved plan, candidate workspace | changes, scores, `optimization_report.md` | Accept, continue, rollback, or re-plan. |

Meta skills in `core_skills/00_meta/` can run after any stage.

## 4. Artifact Flow

```text
eval_input.csv
  + runner_output.csv
  + traces/*.json
      |
      v
analysis_manifest.json
      |
      v
case_report.md + feedback.json
      |
      v
fix_plan.md
      |
      v
candidate changes + progressive_log.json
      |
      v
optimization_report.md
```

Artifact rules:

- A downstream stage consumes the previous stage's confirmed artifact.
- If an artifact is revised after human review, record the reviewer decision.
- Do not hide unresolved uncertainty. Mark it as open risk or return to the
  previous stage.

## 5. S1: Prepare Evidence

Purpose:

- freeze which cases are in scope,
- collect runner output and traces,
- clean obviously unsafe trace fields,
- create a manifest that downstream stages can consume.

Required output:

- `analysis_manifest.json` with dataset path, selected case IDs, trace paths,
  schema notes, run metadata, and review status.

Failure modes:

- missing expected behavior,
- trace/output mismatch,
- ambiguous case IDs,
- private data in input material,
- non-reproducible runner command.

## 6. S2: Analyze Failures

Purpose:

- explain expected vs observed behavior,
- identify the most likely failure location,
- separate evidence from hypothesis,
- produce both human-readable and machine-readable feedback.

Required outputs:

- `case_report.md` for reviewers,
- `feedback.json` for planning.

Attribution should name one primary failure mode when evidence allows it. If the
evidence is insufficient, the correct result is `needs_more_evidence`, not a
confident guess.

## 7. S3: Plan Fixes

Purpose:

- translate case feedback into focused candidate fixes,
- group fixes into reviewable batches,
- define validation and rollback,
- make tradeoffs explicit before touching implementation files.

Required output:

- `fix_plan.md` with fix IDs, rationale, target artifacts, risk level,
  validation commands, success criteria, and rollback notes.

The plan must be approved before S4 starts.

## 8. S4: Execute and Validate

Purpose:

- apply approved fixes,
- run targeted evaluation,
- compare candidate behavior against baseline,
- detect regressions,
- decide whether to continue, stop, rollback, or return to planning.

Required outputs:

- candidate changes,
- score outputs,
- `progressive_log.json`,
- `optimization_report.md`.

Decision paths:

- Path A: scores improve and no meaningful regression is found; accept or
  continue with the next batch.
- Path B: target improves but regressions appear; revise, split, or roll back
  risky fixes.
- Path C: target does not improve; return to S3 or S2 depending on evidence.

## 9. Human Review Gates

Human gates are embedded in each stage:

- S1 confirms scope.
- S2 confirms attribution.
- S3 approves the plan.
- S4 accepts the outcome.

This keeps the workflow linear while preserving accountability.

## 10. Directory Template

```text
experiments/<experiment_id>/
├── experiment.yaml
├── inputs/
├── s1_prepare/
│   └── analysis_manifest.json
├── s2_analyze/
│   ├── case_reports/
│   └── feedback.json
└── rounds/
    └── round_1/
        ├── fix_plan.md
        ├── progressive_log.json
        ├── scores/
        └── optimization_report.md
```

Public examples may use a smaller layout, but they should preserve artifact
names and stage meaning.

## 11. Productization Notes

Public docs use engineering terms. Product surfaces may later use friendlier
labels such as task, version, change, and result. Keep `experiment_id` stable for
paths and APIs, and use `display_name` for human-facing labels.

## 12. Open Design Questions

- Which trace backends should be supported first after the local synthetic demo?
- How much of S2/S3 should remain document-driven versus become structured JSON?
- Which scoring interfaces should be stable in the first non-alpha release?
