# Contributing

Thanks for your interest in Auto-evoloop. This repository uses public GitHub
workflow conventions and keeps private history, private data, internal endpoints,
and proprietary prompts out of scope.

## Source of Truth

Each durable rule should have one canonical home:

| Information | Source of truth |
| --- | --- |
| Workflow terminology and S1-S4 architecture | `core_skills/DESIGN.md` |
| Public package and demo implementation context | `core_skills/CONTEXT.md` |
| Maintainer migration review inventory | `docs/public-migration-inventory.md` |
| Contribution, branch, review, and release rules | `CONTRIBUTING.md` |
| Security and leak handling | `SECURITY.md` |
| Sanitization boundary | `docs/sanitization-policy.md` |
| CLI usage | `README.md` and `docs/quickstart.md` |

Do not duplicate long policy text across files. Link to the source of truth
instead.

Most contributors only need the sanitization policy and pull request checklist.
The migration inventory is a maintainer-facing review aid for the initial alpha
migration.

## Branching

- Use topic branches for all changes.
- Use the `codex/` prefix for agent-authored branches unless another prefix is
  requested.
- Do not push directly to `main`.
- Keep pull requests small enough to review.

## Commit Rules

- Use clear imperative commit messages, for example `docs: expand public skill contracts`.
- Behavior changes should include tests or validation notes.
- Documentation-only changes should explain what reader decision they improve.
- Generated files, cache directories, and private local artifacts should not be
  committed.

## Public Data Boundary

Before opening a pull request, confirm that it contains no:

- `.env` files, credentials, cookies, tokens, keys, or sessions,
- real user, customer, employee, patient, debtor, contract, payment, health,
  financial, or support conversation data,
- private traces, screenshots, eval reports, or case reports,
- private repository URLs, private package indexes, internal hostnames, or
  deployment details,
- imported private Git history.

Examples and fixtures must be synthetic.

## Skill Document Rules

When changing `core_skills/**/SKILL.md`:

- preserve the public stage contract: purpose, inputs, outputs, procedure, human
  gate, and failure modes,
- keep long templates in `references/`,
- avoid organization-specific names,
- update related templates when the contract changes,
- run `tests/test_core_skills_contract.py`.

## Pull Request Checklist

- Scope is public-safe and reviewable.
- Tests or validation commands are listed.
- Documentation links resolve.
- New examples use synthetic data only.
- README may contain Chinese; other docs should remain English.
- Security-sensitive findings are reported through `SECURITY.md`, not public
  issues.
