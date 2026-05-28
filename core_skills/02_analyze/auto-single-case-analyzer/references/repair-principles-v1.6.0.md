# Repair Principles v1.6.0

1. Prefer the smallest change that can address the observed failure.
2. Repair the boundary where the failure occurs.
3. Preserve behavior that already passes.
4. Avoid broad rewrites when a prompt, schema, guard, or parser fix is enough.
5. Add validation that would have caught the failure.
6. Make rollback possible.
7. Separate target improvement from unrelated cleanup.
8. Treat evaluation-label problems as eval fixes, not agent fixes.

## Risk Levels

- Low: wording, formatting, or local validation improvement.
- Medium: prompt/tool behavior change with narrow scope.
- High: architecture, memory, retrieval, or multi-step policy change.
