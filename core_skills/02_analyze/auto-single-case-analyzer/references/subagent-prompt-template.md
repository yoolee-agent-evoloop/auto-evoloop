# Subagent Prompt Template

Use this template when delegating one case analysis to another agent. Only send
public-safe or approved artifacts.

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
5. Return both a short markdown report and feedback JSON.

Rules:
- Do not invent missing evidence.
- Mark needs_more_evidence when evidence is insufficient.
- Do not include private identifiers or raw sensitive payloads.
```
