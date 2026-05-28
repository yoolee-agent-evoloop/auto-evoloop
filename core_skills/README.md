# Core Skills

`core_skills/` contains the public-safe Auto-evoloop method. These files define
workflow contracts, review gates, and reusable templates. They are not private
run logs, business prompts, trace exports, or historical process notes.

Read order:

1. `DESIGN.md` for the canonical workflow.
2. `CONTEXT.md` for public package and artifact context.
3. `00_meta/entropy-control/CHECKLIST.md` before changing any skill contract.
4. The S1-S4 skill files for stage-specific execution rules.

Stages:

- Meta review: `00_meta/meta-reflection/`
- S1 prepare: `01_prepare/auto-trace-prep/`
- S2 analyze: `02_analyze/auto-single-case-analyzer/`
- S3 plan: `03_plan/auto-fix-planner/`
- S4 execute: `04_execute/auto-fix-executor/`

Deprecated private archive material and generated caches are intentionally not
part of this public tree.
