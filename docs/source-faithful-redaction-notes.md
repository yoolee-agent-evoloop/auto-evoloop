# Source-Faithful Redaction Notes

These notes describe the public-safety patch categories applied after importing
private source files. They intentionally do not quote sensitive source text.

| File or group | Migration note | Redaction categories |
|---|---|---|
| `CONTRIBUTING.md` | Initialized from the private governance file and patched to use platform-neutral public terms. | Internal platform names, private remotes, private package hosts, business names, private reviewer bot names, historical process details. |
| `core_skills/DESIGN.md` | Initialized from the private design file and patched to keep the S1-S4 architecture while generalizing private framework and business examples. | Business names, framework IDs, private package source, trace backend names, private reviewer integration, real experiment references. |
| `core_skills/00_meta/**` | Initialized from private meta-skill files, excluding archives, and patched to keep meta-reflection structure. | Private review links, real calibration round labels, host runtime file names, business-specific examples. |
| `core_skills/01_prepare/auto-trace-prep/**` | Initialized from private S1 files and patched to keep artifact contracts while abstracting trace and eval setup. | Trace backend credentials, project IDs, framework IDs, service URLs, private agent-source paths, business names. |
| `core_skills/02_analyze/auto-single-case-analyzer/**` | Initialized from private S2 files and patched to keep attribution and HITL feedback structure. | Business scorer prompt names, real rubric examples, model/vendor names, trace backend names, private case details. |
| `core_skills/03_plan/auto-fix-planner/**` | Initialized from private S3 files and patched to add an explicit authorization gate before reviewer delegation. | Private reviewer tooling, model/vendor names, business component names, historical round examples, private path examples. |
| `core_skills/04_execute/auto-fix-executor/**` | Initialized from private S4 files and patched to keep D1/D2, progressive logs, and evaluator feedback contracts. | Business scorer prompt names, credential paths, business file examples, private framework IDs, real report references. |
| `core_skills/CONTEXT.md` | Not source-imported. The public-authored summary remains in place. | Private continuation context excluded in full. |
