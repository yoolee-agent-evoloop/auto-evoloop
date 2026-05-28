# Attribution-to-Plan Framework

S3 consumes S2 attribution without copying private examples or upstream repair
suggestions.

## Canonical Fields

- `scope`
- `component`
- `rule_violation`
- `description`
- `evidence`
- `trace_refs`
- `causal_edges`
- `target_layer`
- `fix_strategy`

## Planning Rules

- `scope=external` becomes an external issue, not an automatic fix.
- Every fix must map back to evidence.
- The first plan should prefer the smallest useful repair.
- High-risk fixes require stronger validation and rollback notes.
