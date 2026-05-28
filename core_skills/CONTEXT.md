# Auto-evoloop Developer Context

This document helps contributors understand how the public package and
methodology documents fit together.

## Current Public Scope

The public repository contains:

- a Python CLI for demos, sampling, scoring, comparison, and trace cleaning,
- a fully synthetic offline demo,
- public-safe S1-S4 skill contracts,
- templates and checklists that preserve the workflow shape without private
  business data.

The public repository does not contain:

- private business projects,
- real eval datasets or trace exports,
- proprietary prompts,
- private package indexes,
- deployment-specific runners.

## Package Modules

| Module | Role |
| --- | --- |
| `auto_evoloop.cli` | Typer-based CLI entry point. |
| `auto_evoloop.demo.run` | End-to-end synthetic demo. |
| `auto_evoloop.sampling.extract_sample` | Deterministic subset extraction from CSV evals. |
| `auto_evoloop.scoring.score` | Local scorer and reserved LLM scorer interface. |
| `auto_evoloop.reporting.compare` | Baseline/candidate score comparison. |
| `auto_evoloop.traces.clean` | Public-safe trace redaction helper. |
| `auto_evoloop.traces.langfuse_fetch` | Placeholder contract for future trace backends. |

## Artifact Contracts

The methodology is file-first. A stage should be callable from a fresh context if
the required input files exist.

| Artifact | Minimal fields |
| --- | --- |
| `analysis_manifest.json` | `experiment_id`, `selected_cases`, `schema`, `trace_files`, `review_status` |
| `feedback.json` | `case_id`, `finding`, `evidence`, `failure_mode`, `repair_hint`, `confidence` |
| `fix_plan.md` | objective, fix list, validation plan, risk notes, rollback notes, approval state |
| `progressive_log.json` | batch ID, fixes applied, commands, scores, regression notes, decision |
| `optimization_report.md` | summary, changes, score delta, regressions, open risks, next steps |

## Run Metadata

Every non-trivial run should record:

- package version or Git commit,
- command and arguments,
- input paths,
- output paths,
- timestamp,
- environment notes,
- scorer type.

This does not guarantee exact reproduction for LLM-based systems, but it makes
review possible.

## Development Invariants

- Examples remain synthetic.
- Public docs remain English, except README which is bilingual.
- Core skill contracts should not mention private organizations, private
  repositories, private package indexes, or private endpoints.
- Trace cleaning is a defense-in-depth helper, not a privacy guarantee.
- A plan is not executable until its human approval state is explicit.

## Recommended Local Checks

```bash
python -m pip install -e ".[dev]"
pytest
evoloop demo run
evoloop trace clean --input examples/synthetic_demo/synthetic_trace.json --output /tmp/synthetic_trace.clean.json
```
