# Skill Entropy-Control Checklist

Use this checklist whenever a pull request changes `core_skills/**/SKILL.md`.
The goal is to keep skill files executable and reviewable instead of letting them
turn into mixed notes, logs, and one-off instructions.

## Required Checks

- The trigger condition is explicit.
- Inputs and outputs are named as files or structured fields.
- The stage boundary is clear.
- Human review gates are explicit.
- Failure modes are listed.
- Long examples and templates live in `references/`.
- Implementation details that may change live outside the core contract.
- No private organizations, private repository URLs, internal hostnames, real
  customer data, credentials, or deployment details appear.
- Any new term is either defined in `DESIGN.md` or avoided.
- The document tells the next agent what to do, not what happened once.

## Red Flags

- "For now" instructions with no expiry.
- One-off incident summaries.
- Hidden dependencies on chat history.
- Business-specific examples.
- Large pasted reports that should be artifacts.
- Duplicated policy text from another source of truth.

## Reviewer Decision

Choose one:

- `PASS`: contract stays clear and public-safe.
- `PASS_WITH_NITS`: only wording or link issues remain.
- `REVISE`: stage boundary, privacy, or artifact contract is unclear.
