# Auto-evoloop Core Design

This document is the source of truth for the public Auto-evoloop workflow. It is
public-authored from the method, not copied from private repository history.
Business projects, real traces, private prompts, internal endpoints, and
deployment details are intentionally out of scope.

## Terminology

Auto-evoloop uses four workflow layers:

| Layer | Term | Definition |
| --- | --- | --- |
| L1 | Experiment | One improvement cycle around an evaluation input and a goal. |
| L2 | Round | One approved fix plan and one execution attempt. |
| L3 | Batch | A group of fixes applied and evaluated together inside a round. |
| L4 | Fix | One focused behavior, prompt, tool, or configuration change. |

`evoloop` is the project name, not a workflow layer. Use the terms above in
paths, reports, logs, and review comments.

## Goals

- Make agent improvement reproducible through files and commands.
- Separate evidence preparation, case analysis, fix planning, and execution.
- Keep human review gates explicit.
- Prefer small, validated changes before broader redesign.
- Keep public examples synthetic and safe to run offline.

## Stage Overview

| Stage | Skill | Required output | Human gate |
| --- | --- | --- | --- |
| S1 | `auto-trace-prep` | `analysis_manifest.json` | Confirm case scope, schema, and trace safety. |
| S2 | `auto-single-case-analyzer` | `case_report.md`, `feedback.json` | Confirm attribution quality. |
| S3 | `auto-fix-planner` | `fix_plan.md` | Approve, revise, or reject the plan. |
| S4 | `auto-fix-executor` | `progressive_log.json`, `optimization_report.md` | Accept, continue, roll back, or re-plan. |

Meta skills in `00_meta/` can run after any stage.

## Artifact Flow

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

- A downstream stage consumes the previous stage's reviewed artifact.
- If a human revises an artifact, record the decision in that artifact or an
  adjacent review note.
- If evidence is insufficient, return to the previous stage instead of hiding
  uncertainty.

## Idempotency

Each stage is structurally idempotent:

- Inputs are files or explicit command arguments.
- Outputs use stable artifact names.
- Re-running a stage with the same inputs should preserve the same artifact
  shape.
- LLM text, agent behavior, and scores may vary; record run metadata so humans
  can interpret differences.

## S1: Prepare Evidence

S1 freezes the analysis scope. It selects cases, maps schema fields, links runner
outputs and traces, and creates `analysis_manifest.json`.

Required manifest fields:

- `experiment_id`
- `display_name`
- `schema`
- `selected_cases`
- `trace_files`
- `run_metadata`
- `review_status`

S1 stops when case IDs are ambiguous, expected behavior is missing, trace files
cannot be matched, or private data is present in public-bound material.

## S2: Analyze Failures

S2 analyzes one case at a time. It states expected behavior, observed behavior,
evidence, failure mode, alternative hypotheses, and a small repair hint.

The correct output for weak evidence is `needs_more_evidence`, not a confident
guess.

## S3: Plan Fixes

S3 converts S2 findings into a reviewable `fix_plan.md`. A fix plan must map
each fix to evidence, name target artifacts, define validation, state risk, and
include rollback notes.

S4 must not execute a draft or unapproved plan.

## S4: Execute and Validate

S4 applies approved fixes, runs evaluation, scores outputs, compares baseline
and candidate behavior, and writes `optimization_report.md`.

Decision paths:

- Accept when target behavior improves and meaningful regressions are absent.
- Continue when improvement is partial and the next approved fix is low risk.
- Roll back when regressions outweigh gains.
- Return to S3 or S2 when the plan or attribution no longer matches evidence.

## Directory Template

```text
experiments/<experiment_id>/
+-- experiment.yaml
+-- inputs/
+-- s1_prepare/
|   +-- analysis_manifest.json
+-- s2_analyze/
|   +-- case_reports/
|   +-- feedback.json
+-- rounds/
    +-- round_1/
        +-- fix_plan.md
        +-- progressive_log.json
        +-- scores/
        +-- optimization_report.md
```

Public examples may use a smaller layout, but should keep the artifact meaning.
