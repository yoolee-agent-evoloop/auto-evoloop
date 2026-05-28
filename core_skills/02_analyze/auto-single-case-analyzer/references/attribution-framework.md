# Attribution Framework

Attribution should answer: where did the behavior diverge, what evidence proves
that, and what is the smallest useful repair direction?

## Evidence Levels

| Level | Meaning | Use |
| --- | --- | --- |
| Direct | Trace/output explicitly shows the failure. | Strong basis for planning. |
| Comparative | Baseline/candidate or pass/fail cases differ in a meaningful way. | Good basis when direct trace is incomplete. |
| Contextual | Schema, prompt, or tool contract suggests likely cause. | Use with caution. |
| Missing | Required evidence is unavailable. | Mark `needs_more_evidence`. |

## Attribution Steps

1. Locate the first observable divergence.
2. Tie it to a stage, prompt, tool, model output, parser, or eval label.
3. Check whether the failure repeats across similar cases.
4. Identify alternative hypotheses.
5. Choose the narrowest failure mode supported by evidence.

## Output Rule

Do not write a confident root cause unless at least one direct or comparative
evidence item supports it.
