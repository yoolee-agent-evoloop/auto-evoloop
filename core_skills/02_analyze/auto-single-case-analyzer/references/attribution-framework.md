# Attribution Framework

Attribution answers where behavior diverged, which evidence proves it, and what
small repair direction follows.

## Evidence Levels

| Level | Meaning |
| --- | --- |
| Direct | Trace or output explicitly shows the failure. |
| Comparative | Baseline, candidate, pass, or fail cases differ meaningfully. |
| Contextual | Schema, prompt, or tool contract suggests a likely cause. |
| Missing | Required evidence is unavailable. |

## Procedure

1. Locate the first observable divergence.
2. Tie it to a stage, prompt, tool, model output, parser, or eval label.
3. Check whether the failure repeats across similar cases.
4. Identify alternative hypotheses.
5. Choose the narrowest failure mode supported by evidence.

Do not state a confident root cause without direct or comparative evidence.
