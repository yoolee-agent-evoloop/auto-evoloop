# Scorer Feedback Template

Use this when a scorer result needs human-readable explanation.

```json
{
  "case_id": "",
  "score": 0,
  "passed": false,
  "reason": "",
  "expected": "",
  "observed": "",
  "rubric_notes": "",
  "requires_human_review": false
}
```

## Review Rules

- A low score should explain the violated expectation.
- A pass should still preserve enough reason for audit.
- If the expected behavior is ambiguous, mark `requires_human_review`.
- Scorer feedback must not include private raw payloads.
