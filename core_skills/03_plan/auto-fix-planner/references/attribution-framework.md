# Attribution-to-Plan Mapping

S3 consumes S2 attribution. It should preserve evidence links instead of
rewriting findings into unsupported implementation ideas.

## Mapping Table

| S2 failure mode | Typical planning focus |
| --- | --- |
| `instruction_following` | Prompt instruction, priority, examples, or guardrails. |
| `retrieval_or_context` | Context selection, ranking, chunking, or missing source handling. |
| `tool_use` | Tool schema, tool choice policy, argument validation, fallback handling. |
| `reasoning` | Decomposition, intermediate checks, or verification steps. |
| `format_or_schema` | Output parser, schema examples, field validation, serializer. |
| `safety_or_policy` | Refusal policy, escalation rule, unsafe content handling. |
| `evaluation_or_label` | Eval label, scorer, rubric, or expected output correction. |
| `needs_more_evidence` | Return to S1/S2 before planning. |

## Planning Rule

If the failure mode is `needs_more_evidence`, do not invent a fix. Ask for more
evidence or reduce the plan to instrumentation.
