# Reviewer Findings Schema

Use this schema when a human or reviewer adapter returns plan feedback.

```json
{
  "reviewer": "",
  "decision": "approve|revise|reject|needs_more_analysis",
  "findings": [
    {
      "severity": "p0|p1|p2",
      "fix_id": "FIX_001",
      "issue": "",
      "required_change": ""
    }
  ],
  "approved_validation_scope": [],
  "notes": ""
}
```

Reviewer adapters that send data outside the local machine require explicit user
authorization.
