# Repair Principles v1.6.0

This file mirrors the S2 repair principles so S3 can plan without duplicating
the whole analyzer reference.

1. Prefer the smallest change that addresses the observed failure.
2. Repair the boundary where the failure occurs.
3. Preserve passing behavior.
4. Avoid broad rewrites when targeted instructions, schema checks, or tool
   guards are enough.
5. Add validation that would have caught the issue.
6. Keep rollback simple.
7. Separate product decisions from implementation fixes.
8. Treat evaluator mistakes as evaluator fixes.

## Planning Implication

Every high-risk fix must include:

- why lower-risk fixes are insufficient,
- validation beyond the original failing cases,
- rollback notes.
