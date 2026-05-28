# Auto-evoloop Public Context

This document describes the public package and methodology context. It is not a
continuation log from the private repository.

## Public Scope

Included:

- Python CLI for local demo, sampling, scoring, comparison, and trace cleaning.
- Synthetic offline example data.
- Public-safe S1-S4 skill contracts.
- Templates and checklists for reviewable agent improvement.

Excluded:

- Real evaluation data or trace exports.
- Business prompts and customer/user records.
- Private repository history.
- Internal endpoints, package indexes, deployment details, and credentials.

## Package Modules

| Module | Role |
| --- | --- |
| `auto_evoloop.cli` | Typer-based command entry point. |
| `auto_evoloop.demo` | Offline synthetic demo workflow. |
| `auto_evoloop.sampling` | Deterministic CSV subset extraction. |
| `auto_evoloop.scoring` | Local scorer and reserved LLM scorer interface. |
| `auto_evoloop.reporting` | Baseline/candidate comparison and markdown reporting. |
| `auto_evoloop.traces` | Trace cleanup and future trace backend helpers. |

## Artifact Contracts

| Artifact | Purpose |
| --- | --- |
| `analysis_manifest.json` | Freezes S1 case selection, schema, trace paths, and review status. |
| `feedback.json` | Carries S2 structured findings into S3. |
| `fix_plan.md` | Defines approved fixes, validation, risk, and rollback. |
| `progressive_log.json` | Records S4 batches, commands, scores, regressions, and decisions. |
| `optimization_report.md` | Summarizes final outcome, score delta, risk, and next actions. |

## Development Invariants

- Examples remain synthetic.
- README may be bilingual; other public docs stay English.
- Trace cleaning is defense in depth, not a privacy guarantee.
- A plan is executable only after approval is explicit.
- Private data must be excluded before any file enters this public repository.
