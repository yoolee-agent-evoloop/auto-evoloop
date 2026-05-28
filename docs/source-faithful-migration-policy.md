# Source-Faithful Migration Policy

Alpha.2 changes the public migration strategy for core methodology files.

## Policy

- Core methodology files are initialized from the private source file, then edited with the smallest public-safety patch that removes or generalizes private material.
- Core methodology files may keep their original Chinese wording, structure, terms, and information density.
- `README.md` remains bilingual. Non-core public docs remain English.
- `core_skills/CONTEXT.md` is not migrated from the private source file because it is a private continuation context. The public repository keeps a public-authored implementation summary instead.
- Alpha.1 remains a valid transitional release, but its public-authored rewrites are superseded by the source-faithful Alpha.2 methodology migration.

## Redaction Rules

Remove or generalize:

- internal platform names, private remotes, private package hosts, deployment paths, and private reviewer bot names,
- business names, business project directories, business prompts, real case/session/turn IDs, real traces, evals, and reports,
- environment files, credentials, cookies, private keys, API keys, and credential paths,
- one-off process drafts, real experiment dates, and version-migration details that cannot be published.

Preserve:

- original Chinese headings and body text when safe,
- S1-S4 stage contracts, artifact names, HITL gates, D1/D2 decisions, and Experiment/Round/Batch/FIX terminology,
- template structure, field names, quality gates, rollback, circuit-breaker, and review workflows.

## Review Gate

Every source-faithful batch must include:

- a diff review against the public branch,
- a private keyword scan performed locally by maintainers,
- a credential-pattern scan,
- tests and the synthetic demo,
- a patch-note entry that names redaction categories without quoting sensitive source text.
