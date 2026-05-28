# Contributing

Thanks for your interest in Auto-evoloop.

This repository is currently being prepared for its first clean source release. Until then, contributions should focus on public documentation, project hygiene, and issue discussion.

## Development Principles

- Keep the public repository free of private data, customer data, credentials, internal endpoints, and proprietary business prompts.
- Prefer small, reviewable pull requests.
- Include tests or validation notes for behavior changes.
- Keep examples synthetic and clearly marked as examples.
- Re-check `.gitignore` when adding source, examples, or fixtures so useful public assets are not accidentally hidden.
- Use Apache-2.0 licensing for project-owned source files. Prefer SPDX headers for new source files when the language ecosystem commonly supports them.

## Pull Request Checklist

Before opening a pull request, confirm that:

- No `.env` file, secret, token, private key, cookie, trace export, or production endpoint is included.
- No real user, customer, employee, patient, debtor, contract, payment, health, financial, or support conversation data is included.
- No private repository history has been imported.
- New examples use synthetic data only.
- Documentation changes are clear to readers who do not know the internal project history.

## Reporting Security Issues

Use the process in [SECURITY.md](SECURITY.md). Do not disclose sensitive findings in public issues or pull requests.
