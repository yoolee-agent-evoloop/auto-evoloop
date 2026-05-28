# Public Migration Inventory

This document defines the first review gate for migrating private Auto-evoloop
assets into this public repository.

It intentionally contains only paths, target locations, migration status, and
sanitization risk labels. It does not copy private document text, prompts, trace
content, eval data, case reports, endpoints, credentials, or repository history.

## Target Public Structure

```text
auto-evoloop/
+-- auto_evoloop/                  # Public Python package and CLI
+-- core_skills/                   # Public-safe method and skill contracts
|   +-- DESIGN.md                  # Canonical open workflow design
|   +-- CONTEXT.md                 # Public developer context and artifact map
|   +-- 00_meta/                   # Cross-stage checks and meta reflection
|   +-- 01_prepare/                # S1 evidence preparation
|   +-- 02_analyze/                # S2 case analysis and optional summary
|   +-- 03_plan/                   # S3 fix planning
|   +-- 04_execute/                # S4 execution and validation
+-- docs/                          # Public docs, policies, and migration reviews
+-- examples/synthetic_demo/       # Synthetic examples only
+-- tests/                         # CLI and public contract tests
```

## Status Labels

| Status | Meaning |
| --- | --- |
| `migrate_as_public_safe` | Path appears safe to migrate with light wording review. |
| `sanitize_required` | Keep most structure, but remove or generalize sensitive details. |
| `rewrite_required` | Preserve intent, but rewrite for public readers before migration. |
| `exclude` | Do not migrate to the public repository. |
| `list_only` | Track as a candidate now; migrate content only after a later review. |

## Risk Labels

| Risk | Meaning |
| --- | --- |
| `business_data` | May include real customer/user/domain facts. |
| `internal_platform` | May mention internal hosting, review, package, or deployment systems. |
| `private_repo_path` | May reveal private repository names, remotes, or local delivery layout. |
| `real_trace_eval` | May include real trace, eval, score, report, or case material. |
| `business_prompt` | May include proprietary prompt or agent behavior content. |
| `credential_risk` | May include environment variables, tokens, secrets, cookies, or key paths. |
| `process_draft` | Historical or one-off process material that should not become public docs. |
| `low_risk` | No obvious sensitive category from path-level review. |

## Core Document Candidates

| Private source path | Proposed public target | Status | Risks | Review note |
| --- | --- | --- | --- | --- |
| `CONTRIBUTING.md` | `CONTRIBUTING.md` | `rewrite_required` | `internal_platform`, `private_repo_path` | Preserve governance intent, but rewrite for public GitHub-only workflow. |
| `core_skills/DESIGN.md` | `core_skills/DESIGN.md` | `rewrite_required` | `business_data`, `internal_platform`, `private_repo_path`, `process_draft` | Preserve S1-S4 design and terminology, but author a public design instead of copying private migration history. |
| `core_skills/CONTEXT.md` | none | `exclude` | `business_data`, `internal_platform`, `private_repo_path`, `real_trace_eval`, `process_draft` | Treat as private continuation context; any future public context should be newly authored from public package facts. |

## Core Skill Candidates

| Private source path | Proposed public target | Status | Risks | Review note |
| --- | --- | --- | --- | --- |
| `core_skills/00_meta/entropy-control/CHECKLIST.md` | same path | `sanitize_required` | `internal_platform`, `process_draft` | Reusable checklist, but remove private review links and historical examples. |
| `core_skills/00_meta/meta-reflection/SKILL.md` | same path | `migrate_as_public_safe` | `low_risk` | General meta-process contract with low path-level sensitivity. |
| `core_skills/00_meta/meta-reflection/stages/S1.md` | same path | `migrate_as_public_safe` | `low_risk` | General S1 review module. |
| `core_skills/00_meta/meta-reflection/stages/S2.md` | same path | `migrate_as_public_safe` | `low_risk` | General attribution review module. |
| `core_skills/00_meta/meta-reflection/stages/S3.md` | same path | `migrate_as_public_safe` | `low_risk` | General planning review module. |
| `core_skills/00_meta/meta-reflection/stages/S4.md` | same path | `sanitize_required` | `business_data`, `real_trace_eval` | Keep validation review structure; remove private artifact path examples. |
| `core_skills/00_meta/meta-reflection/references/output-template.md` | same path | `migrate_as_public_safe` | `low_risk` | General output template. |
| `core_skills/00_meta/meta-reflection/references/human-review-checklist.md` | same path | `migrate_as_public_safe` | `low_risk` | General human review checklist. |
| `core_skills/00_meta/meta-reflection/_archive/**` | none | `exclude` | `process_draft` | Historical archive should not seed the public repo. |
| `core_skills/01_prepare/auto-trace-prep/SKILL.md` | same path | `sanitize_required` | `real_trace_eval`, `internal_platform` | Preserve S1 contract; remove private trace backend specifics. |
| `core_skills/01_prepare/auto-trace-prep/references/*.md` | same paths | `sanitize_required` | `internal_platform`, `real_trace_eval` | Keep only generic environment/setup guidance. |
| `core_skills/01_prepare/auto-trace-prep/scripts/*.py` | `auto_evoloop/traces/` or same path | `list_only` | `credential_risk`, `internal_platform`, `real_trace_eval` | Track as candidate; migrate only after code-level sanitization review. |
| `core_skills/01_prepare/auto-trace-prep/scripts/__pycache__/**` | none | `exclude` | `process_draft` | Generated cache files must not migrate. |
| `core_skills/02_analyze/auto-single-case-analyzer/SKILL.md` | same path | `sanitize_required` | `business_data`, `business_prompt`, `real_trace_eval` | Preserve S2 contract; remove private examples and prompt-specific language. |
| `core_skills/02_analyze/auto-single-case-analyzer/references/*.md` | same paths | `sanitize_required` | `business_prompt`, `real_trace_eval` | Keep attribution, repair, report, and delegation templates after sanitization. |
| `core_skills/02_analyze/auto-single-case-analyzer/scripts/*.py` | same path or `auto_evoloop/reporting/` | `list_only` | `real_trace_eval` | Track viewer generator as a later utility candidate; runtime input can still be sensitive. |
| `core_skills/02_analyze/auto-single-case-analyzer/viewer/*.html` | same path or `examples/` | `list_only` | `real_trace_eval`, `business_prompt` | Migrate only if sample data, labels, and UI copy are synthetic. |
| `core_skills/02_analyze/auto-single-case-analyzer/viewer/tests/fixtures/**` | same path or `examples/` | `migrate_as_public_safe` | `low_risk` | Explorer review suggests these are synthetic fixtures; still verify before copying. |
| `core_skills/02_analyze/auto-case-summary/SKILL.md` | none | `exclude` | `process_draft` | Deprecated helper with low migration value. |
| `core_skills/02_analyze/auto-case-summary/references/*.md` | none | `exclude` | `process_draft`, `business_prompt` | Tied to deprecated summary flow and may include business-like examples. |
| `core_skills/03_plan/auto-fix-planner/SKILL.md` | same path | `sanitize_required` | `business_prompt`, `private_repo_path` | Preserve S3 plan contract; remove private source/worktree assumptions. |
| `core_skills/03_plan/auto-fix-planner/references/*.md` | same paths | `sanitize_required` | `business_prompt`, `real_trace_eval` | Keep public repair principles and fix-plan templates. |
| `core_skills/04_execute/auto-fix-executor/SKILL.md` | same path | `sanitize_required` | `internal_platform`, `private_repo_path`, `real_trace_eval` | Preserve S4 execution contract; remove private eval runner and platform assumptions. |
| `core_skills/04_execute/auto-fix-executor/references/*.md` | same paths | `sanitize_required` | `real_trace_eval` | Keep public optimization/scorer feedback templates. |

## General Script Candidates

| Private source path | Proposed public target | Status | Risks | Review note |
| --- | --- | --- | --- | --- |
| `scripts/score/compare.py` | `auto_evoloop/reporting/compare.py` | `migrate_as_public_safe` | `low_risk` | Local CSV comparison tool; compare with existing public module before copying. |
| `scripts/score/score.py` | `auto_evoloop/scoring/score.py` | `sanitize_required` | `business_prompt`, `internal_platform`, `real_trace_eval` | Reusable shape, but remove hard-coded service defaults and document data egress. |
| `scripts/score/score_guide.md` | `docs/` or package docs | `sanitize_required` | `internal_platform`, `credential_risk`, `real_trace_eval`, `business_prompt` | Convert to generic CLI docs if useful. |
| `scripts/score/*_score.md` | none | `exclude` | `business_data`, `business_prompt`, `real_trace_eval` | Business-specific scorer docs are out of public scope. |
| `scripts/score/.env` | none | `exclude` | `credential_risk` | Environment files must never migrate. |
| `scripts/small_sample/extract_sample.py` | `auto_evoloop/sampling/extract_sample.py` | `sanitize_required` | `real_trace_eval`, `business_data` | Function is generic, but examples and names need neutralization before migration. |
| `scripts/small_sample/extract_sample_guide.md` | `docs/` or package docs | `sanitize_required` | `real_trace_eval` | Convert to generic sample extraction guide if needed. |
| `scripts/small_sample/run_sample.ps1` | `examples/` or `scripts/` | `list_only` | `internal_platform`, `real_trace_eval` | Only migrate if it can run against synthetic examples. |
| `scripts/traces_fetch/fetch_and_clean.py` | `auto_evoloop/traces/` | `sanitize_required` | `credential_risk`, `internal_platform`, `real_trace_eval` | Reusable trace-fetch shape, but default output can contain sensitive trace data. |
| `scripts/traces_fetch/fetch_trace.py` | `auto_evoloop/traces/` | `rewrite_required` | `credential_risk`, `internal_platform`, `real_trace_eval` | Direct backend export should be abstracted and made safe-by-default before public use. |
| `scripts/traces_fetch/*_guide.md` | `docs/` | `sanitize_required` | `credential_risk`, `internal_platform` | Rewrite as public trace adapter guidance, not internal setup instructions. |
| `core_skills/01_prepare/auto-trace-prep/scripts/traces_fetch.py` | `auto_evoloop/traces/` | `rewrite_required` | `credential_risk`, `internal_platform`, `real_trace_eval` | Most complete trace export candidate, but needs parameterization, redaction, and query safety review. |

## Explicit Exclusions

| Path or content family | Status | Risks | Reason |
| --- | --- | --- | --- |
| `projects/**` | `exclude` | `business_data`, `business_prompt`, `real_trace_eval` | Business project material is not part of the public bootstrap. |
| `.env`, `.env.*`, key files, cookies, sessions | `exclude` | `credential_risk` | Secrets and local runtime state must never migrate. |
| Real traces, eval outputs, score reports, and case reports | `exclude` | `real_trace_eval`, `business_data` | Public examples must be synthetic. |
| Private Git history | `exclude` | `private_repo_path`, `internal_platform` | Public repo uses clean history only. |
| Internal platform configuration or deployment details | `exclude` | `internal_platform`, `private_repo_path` | Public docs should describe portable concepts only. |
| Historical process drafts and archives | `exclude` | `process_draft` | Do not turn one-off history into public source of truth. |

## Review Workflow

1. Review and adjust this inventory.
2. For each `sanitize_required` file, inspect content privately and record the
   required redactions before copying any text.
3. For each `rewrite_required` file, write a public version from the intent,
   not from copied private prose.
4. For each `list_only` script, compare behavior against existing public package
   modules before deciding whether any code should migrate.
5. Open small follow-up PRs by stage or subsystem. Do not combine inventory,
   sanitization, and full migration in one PR.
