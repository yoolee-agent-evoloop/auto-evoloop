# Repair Principles

1. Prefer the smallest change that addresses the observed failure.
2. Repair the boundary where the failure occurs.
3. Preserve passing behavior.
4. Avoid broad rewrites when targeted instructions, schema checks, or tool guards
   are enough.
5. Add validation that would have caught the issue.
6. Keep rollback simple.
7. Separate product decisions from implementation fixes.
8. Treat evaluator mistakes as evaluator fixes.

## Risk Levels

- Low: local wording, schema, or validation improvement.
- Medium: prompt, tool, routing, or scoring behavior change with narrow scope.
- High: architecture, memory, retrieval, or multi-step policy change.
