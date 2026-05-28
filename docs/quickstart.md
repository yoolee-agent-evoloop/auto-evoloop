# Quickstart

```bash
git clone https://github.com/yoolee-agent-evoloop/auto-evoloop.git
cd auto-evoloop
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
evoloop demo run
```

The demo writes generated artifacts to `/tmp/auto-evoloop-demo/`.

Useful commands:

```bash
evoloop --help
evoloop demo run --scorer local
evoloop sample extract --input examples/synthetic_demo/input.csv --output /tmp/sample.csv --sessions 1,2
evoloop trace clean --input examples/synthetic_demo/synthetic_trace.json --output /tmp/synthetic_trace.clean.json
```
