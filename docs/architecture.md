# Architecture

The public alpha has two layers:

- `auto_evoloop/`: executable Python package and CLI.
- `core_skills/`: public-safe methodology that describes how to run the
  improvement loop with durable artifacts.

## Workflow

```text
eval input
  -> runner
  -> trace/output collection
  -> S1 prepare
  -> S2 analyze
  -> S3 plan
  -> S4 execute
  -> score
  -> compare
  -> optimization report
```

## Package Mapping

| Package module | Responsibility |
| --- | --- |
| `auto_evoloop.demo` | Offline synthetic demo runner. |
| `auto_evoloop.runners` | Runner adapter placeholders for agent execution. |
| `auto_evoloop.traces` | Trace cleanup and future trace backend helpers. |
| `auto_evoloop.sampling` | Deterministic eval subset extraction. |
| `auto_evoloop.scoring` | Local scoring and reserved LLM-scoring interface. |
| `auto_evoloop.reporting` | Baseline/candidate comparison and markdown reports. |

## Skill Mapping

| Stage | Skill | Responsibility |
| --- | --- | --- |
| Meta | `meta-reflection` | Stage-exit quality check across S1-S4. |
| S1 | `auto-trace-prep` | Prepare selected eval cases, traces, and manifest. |
| S2 | `auto-single-case-analyzer` | Attribute failures case by case. |
| S2 summary | `auto-case-summary` | Deprecated aggregation helper; retained for migration context. |
| S3 | `auto-fix-planner` | Turn evidence into an approved fix plan. |
| S4 | `auto-fix-executor` | Apply fixes, evaluate, compare, and report. |

## Public Alpha Boundaries

The alpha intentionally avoids private adapters and production deployment
details. Runner and trace integrations are represented by public-safe contracts
and local synthetic examples. External teams can add adapters without changing
the artifact model as long as they preserve the S1-S4 contracts.
