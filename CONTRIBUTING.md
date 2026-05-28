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
| Contribution, branch, review, and release rules | `CONTRIBUTING.md` |
| Security and leak handling | `SECURITY.md` |
| Sanitization boundary | `docs/sanitization-policy.md` |
| CLI usage | `README.md` and `docs/quickstart.md` |

Do not duplicate long policy text across files. Link to the source of truth
instead.

## Repository Shape

```text
auto-evoloop/
├── auto_evoloop/                 # Python package and CLI implementation
├── core_skills/                  # Public-safe Auto-evoloop methodology
│   ├── DESIGN.md                 # Canonical workflow design
│   ├── CONTEXT.md                # Developer context and artifact contracts
│   ├── 00_meta/                  # Cross-stage review and quality controls
│   ├── 01_prepare/               # S1 evidence preparation
│   ├── 02_analyze/               # S2 case analysis and summary
│   ├── 03_plan/                  # S3 fix planning
│   └── 04_execute/               # S4 execution and validation
├── docs/                         # Public docs, policies, and migration notes
├── examples/synthetic_demo/      # Synthetic offline example
└── tests/                        # Unit and CLI tests
```

## Branching

- Use topic branches for all changes.
- Use the `codex/` prefix for agent-authored branches unless another prefix is
  requested.
- Do not push directly to `main`.
- Keep pull requests small enough to review.

## Commit Rules

- Use clear imperative commit messages, for example `docs: expand public skill contracts`.
- A behavior change should include tests or a validation note.
- A documentation-only change should explain what reader decision it improves.
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

- preserve the stage contract: purpose, inputs, outputs, steps, human gate, and
  failure modes,
- keep implementation-specific commands in references or package docs,
- avoid organization-specific names,
- update templates and examples in the same pull request when the contract
  changes,
- run the entropy-control checklist in
  `core_skills/00_meta/entropy-control/CHECKLIST.md`.

## Pull Request Checklist

- Scope is public-safe and reviewable.
- Tests or validation commands are listed.
- Documentation links resolve.
- New examples use synthetic data only.
- The README remains bilingual; other docs remain English.
- Security-sensitive findings are reported through `SECURITY.md`, not public
  issues.
