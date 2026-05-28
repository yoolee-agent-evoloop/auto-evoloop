# Alpha.1 Public Migration Plan

This plan turns the `v0.1.0-alpha.0` bootstrap repository into a reviewable
public alpha that exposes the core Auto-evoloop method without importing private
history, business data, internal endpoints, or proprietary prompts.

## Goal

Publish a public-safe, high-fidelity version of the Auto-evoloop core framework:

- design and governance documents that explain the workflow and contribution model,
- executable synthetic demo and CLI retained from alpha.0,
- core skill contracts that preserve the S1-S4 method and artifact boundaries,
- reusable templates, checklists, and stage references,
- bilingual README only; all other documentation remains English.

## Non-goals

- Do not import private Git history.
- Do not include real traces, eval reports, prompts, customer data, or business project
  directories.
- Do not include private repository names, internal hosting platforms, private package
  indexes, deployment topology, or organization-specific review bots.
- Do not claim production readiness.

## Migration Coverage

| Private source family | Public target | Treatment |
| --- | --- | --- |
| Root contribution governance | `CONTRIBUTING.md` | Rewritten as public-safe SoT, branch, PR, artifact, and release governance. |
| Core design document | `core_skills/DESIGN.md`, `docs/architecture.md`, `docs/concepts.md` | Rewritten in English, preserving terminology, S1-S4 flow, HITL, artifacts, and decision paths. |
| Developer context | `core_skills/CONTEXT.md` | Rewritten in English around public package modules and synthetic demo constraints. |
| Core skill specs | `core_skills/**/SKILL.md` | Expanded from stubs into public-safe stage contracts. |
| Skill references/templates | `core_skills/**/references/*.md` | Recreated as sanitized templates and checklists. |
| Meta reflection stages | `core_skills/00_meta/meta-reflection/stages/*.md` | Recreated as stage-exit review modules. |
| Entropy-control checklist | `core_skills/00_meta/entropy-control/CHECKLIST.md` | Recreated as public skill quality checklist. |
| Trace/viewer helper scripts | `core_skills/**/scripts/*`, `viewer/*` | Recreated with synthetic/local-only defaults. |
| README language | `README.md` | English first, Chinese mirror section second. |

## Acceptance Criteria

- README contains both English and Chinese usage/boundary sections.
- Public docs are English except README.
- `core_skills/DESIGN.md` and `core_skills/CONTEXT.md` exist.
- S1-S4 skills include purpose, inputs, outputs, steps, HITL gates, and failure modes.
- References exist for attribution, repair principles, report templates, fix plan
  templates, optimization report templates, scorer feedback, and environment setup.
- Missing core skill family `auto-case-summary` is explicitly documented as deprecated.
- Tests pass.
- Sensitive-term scan finds no private business/project identifiers or credentials.
