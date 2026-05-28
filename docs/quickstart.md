# Quickstart

## Requirements

- Python 3.10 or newer.
- Git.
- No external services are required for the synthetic demo.

## Install

```bash
git clone https://github.com/yoolee-agent-evoloop/auto-evoloop.git
cd auto-evoloop
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Verify

```bash
evoloop --version
evoloop --help
python -m pytest
```

## Run the Offline Demo

```bash
evoloop demo run
```

The demo writes synthetic outputs to `/tmp/auto-evoloop-demo/`, including:

- `demo_output.csv`
- `demo_scores.csv`
- `demo_baseline_scores.csv`
- `demo_compare.md`
- `demo_report.md`

## Notes

- The local scorer is available now.
- LLM scoring is reserved for a future alpha and must document data egress before
  release.
- Trace cleaning is a helper, not a privacy guarantee. Review outputs before
  sharing them publicly.
