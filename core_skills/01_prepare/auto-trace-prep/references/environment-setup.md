# Environment Setup Reference

S1 should run in an environment where inputs and outputs are explicit.

## Minimum Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Synthetic Demo Inputs

Use `examples/synthetic_demo/` for public examples:

- `input.csv`
- `synthetic_trace.json`
- `config.yaml`

## Trace Cleaning

Trace cleaning removes common sensitive keys and large raw payload fields, but it
is not a formal privacy guarantee. Review cleaned output before committing.

```bash
evoloop trace clean \
  --input examples/synthetic_demo/synthetic_trace.json \
  --output /tmp/synthetic_trace.clean.json
```

## Reproducibility Notes

Record:

- command,
- input paths,
- output paths,
- package version or Git commit,
- scorer or runner mode,
- any manual case-selection criteria.
