# Concepts

Auto-evoloop uses a four-layer improvement model:

- **Experiment**: one evaluation dataset plus one improvement goal.
- **Round**: one approved improvement plan and execution attempt.
- **Batch**: a group of fixes evaluated together.
- **Fix**: one focused change to agent behavior, prompts, tools, or configuration.

Supporting terms:

- **Eval input**: CSV rows that freeze session, turn, prompt, context, and expected behavior.
- **Trace**: structured execution evidence from an agent run.
- **Score**: a local or LLM-assisted judgment of whether a row satisfied expectations.
- **Compare**: baseline vs candidate score analysis.
- **Report**: a markdown summary of changes, outcomes, regressions, and next steps.
