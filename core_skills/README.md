# Core Skills

`core_skills/` contains the public-safe Auto-evoloop method. These files are not
private run logs; they are reusable contracts, templates, and checklists for
agent improvement workflows.

Read order:

1. `DESIGN.md` for the canonical workflow.
2. `CONTEXT.md` for package and artifact context.
3. `00_meta/entropy-control/CHECKLIST.md` before editing any `SKILL.md`.
4. S1-S4 skill files when running or extending a stage.

Stages:

- S1 prepare: `01_prepare/auto-trace-prep/`
- S2 analyze: `02_analyze/auto-single-case-analyzer/`
- S3 plan: `03_plan/auto-fix-planner/`
- S4 execute: `04_execute/auto-fix-executor/`

`02_analyze/auto-case-summary/` is retained as a deprecated migration reference
for teams that still aggregate case findings before planning.
