# Architecture

The public alpha follows this workflow:

```text
input -> runner -> trace -> analyzer -> planner -> executor -> score -> compare -> report
```

Package modules map to the workflow:

- `auto_evoloop.runners`: CSV-oriented runner adapters.
- `auto_evoloop.traces`: trace cleanup and future Langfuse helpers.
- `auto_evoloop.sampling`: deterministic eval subset selection.
- `auto_evoloop.scoring`: local scoring and a reserved LLM scoring hook.
- `auto_evoloop.reporting`: comparison and markdown report utilities.
- `auto_evoloop.demo`: offline synthetic demo.

The alpha intentionally avoids a full plugin system. Adapter names are reserved so future releases can add additional trace and runner backends without changing the CLI shape.
