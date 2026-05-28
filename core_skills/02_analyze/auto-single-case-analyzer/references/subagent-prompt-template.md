# Subagent Prompt Template

Use this template when delegating one public-safe case analysis to another
agent.

```text
You are reviewing one Auto-evoloop case.

Inputs:
- case_id:
- expected_behavior:
- observed_behavior:
- trace_excerpt:
- relevant_schema:

Task:
1. Identify direct evidence.
2. State the most likely failure mode.
3. List alternative hypotheses.
4. Recommend the smallest repair direction.

Rules:
- Do not invent missing evidence.
- Mark needs_more_evidence when evidence is insufficient.
- Do not include private identifiers or raw sensitive payloads.
```
