# Auto-evoloop

Auto-evoloop is an open-source framework for evaluating AI agents, analyzing failures, planning targeted fixes, and validating improvements through iterative experiments.

This is a `v0.1-alpha` release: usable for learning, demos, and lightweight local workflows, but not yet a production agent platform. Internal evaluation data, customer conversations, traces, credentials, proprietary prompts, and private deployment code are intentionally excluded.

## Quickstart

```bash
git clone https://github.com/yoolee-agent-evoloop/auto-evoloop.git
cd auto-evoloop
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
evoloop demo run
```

The demo is fully offline and writes synthetic outputs to `/tmp/auto-evoloop-demo/` by default.

## CLI

```bash
evoloop --help
evoloop demo run
evoloop sample extract --input examples/synthetic_demo/input.csv --output /tmp/sample.csv --sessions 1,2
evoloop score --input /tmp/auto-evoloop-demo/demo_output.csv --output /tmp/demo_scores.csv --scorer local
evoloop compare --baseline /tmp/auto-evoloop-demo/demo_baseline_scores.csv --candidate /tmp/auto-evoloop-demo/demo_scores.csv --output /tmp/demo_compare.md
evoloop trace clean --input examples/synthetic_demo/synthetic_trace.json --output /tmp/synthetic_trace.clean.json
```

## What It Is For

Auto-evoloop helps teams structure iterative agent improvement work:

- freeze evaluation inputs,
- run an agent or deterministic demo runner,
- collect traces and outputs,
- score outcomes,
- compare baseline vs candidate behavior,
- plan and validate focused fixes.

The core concepts are documented in [docs/concepts.md](docs/concepts.md), and the workflow architecture is documented in [docs/architecture.md](docs/architecture.md).

## Public Repository Boundary

This repository intentionally contains only public-safe source code, synthetic examples, and sanitized methodology docs.

Do not commit:

- real customer or user conversations,
- health, financial, contract, payment, or support records,
- private trace exports, logs, screenshots, or case reports,
- `.env` files, credentials, cookies, tokens, keys, or sessions,
- internal endpoints, private repositories, or deployment details.

See [docs/sanitization-policy.md](docs/sanitization-policy.md) before contributing.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Security

Please do not open public issues for suspected leaks or vulnerabilities. See [SECURITY.md](SECURITY.md).
