# Release Checklist

Use this checklist before publishing a public prerelease.

## Required Checks

```bash
git diff --check
python -m pytest
evoloop demo run
rg -n "[\\u4e00-\\u9fff]" docs examples pyproject.toml tests
```

Also run a private maintainer keyword scan for internal business names, internal
platform names, private repository paths, and private package hosts. Do not store
those private keyword lists in this public repository.

Chinese text is allowed in `README.md`, `CONTRIBUTING.md`, and `core_skills/**`
because Alpha.2 keeps core methodology files source-faithful.

## Release Notes

Mention:

- the release is a public alpha,
- examples are synthetic,
- S1-S4 automation is represented by public methodology and local tools,
- production adapters, LLM scoring, and trace backend integrations are reserved
  for later alphas,
- no private data, private history, internal endpoints, or business prompts are
  included.
