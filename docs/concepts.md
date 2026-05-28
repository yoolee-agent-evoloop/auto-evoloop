# Concepts

Auto-evoloop uses the terminology in `core_skills/DESIGN.md` as its source of
truth. This page is a short glossary for readers who are starting from the public
package.

## Workflow Layers

| Layer | Term | Meaning |
| --- | --- | --- |
| L1 | Experiment | One improvement cycle around an evaluation input and a goal. |
| L2 | Round | One approved fix plan and one execution attempt. |
| L3 | Batch | A group of fixes applied and evaluated together. |
| L4 | Fix | One focused behavior, prompt, tool, or configuration change. |

## Core Artifacts

| Artifact | Produced by | Purpose |
| --- | --- | --- |
| `analysis_manifest.json` | S1 prepare | Freezes selected cases, schema, trace paths, and review status. |
| `case_report.md` | S2 analyze | Explains expected behavior, observed behavior, evidence, and attribution. |
| `feedback.json` | S2 analyze | Carries structured findings into planning. |
| `fix_plan.md` | S3 plan | Defines approved fixes, validation, risk, and rollback. |
| `progressive_log.json` | S4 execute | Records iterations, commands, scores, regressions, and decisions. |
| `optimization_report.md` | S4 execute | Summarizes outcome, changes, score delta, residual risks, and next steps. |

## Human Gates

- S1 confirms scope and privacy.
- S2 confirms attribution quality.
- S3 approves the fix plan.
- S4 accepts, continues, rolls back, or returns to planning.
