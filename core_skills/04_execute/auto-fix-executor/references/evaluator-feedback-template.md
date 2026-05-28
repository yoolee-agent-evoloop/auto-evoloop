# Evaluator Feedback Template

Use this public-safe schema for score explanations.

```json
{
  "case_id": "",
  "score": 0,
  "passed": false,
  "reason": "",
  "expected": "",
  "observed": "",
  "rubric_notes": "",
  "affects_score": true,
  "requires_human_review": false
}
```

## Rules

- A low score should explain the violated expectation.
- A pass should preserve enough reason for audit.
- Ambiguous expected behavior requires human review.
- Feedback must not include private raw payloads.
