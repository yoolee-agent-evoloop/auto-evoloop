# Skill Entropy-Control Checklist

Use this checklist whenever a pull request changes `core_skills/**/SKILL.md`.
It keeps skill files executable instead of letting them become mixed notes,
historical reports, and one-off instructions.

## Required Checks

- Purpose, inputs, outputs, procedure, human gate, and failure modes are present.
- Stage boundaries match `core_skills/DESIGN.md`.
- Long examples and templates live in `references/`.
- No private organization, repository, endpoint, package index, credential, or
  real data appears.
- Any new term is defined in `DESIGN.md` or avoided.
- The document tells future agents what to do, not what happened once.

## Reviewer Decision

- `PASS`: contract is clear and public-safe.
- `PASS_WITH_NITS`: minor wording or link fixes remain.
- `REVISE`: boundary, privacy, or artifact contract is unclear.
