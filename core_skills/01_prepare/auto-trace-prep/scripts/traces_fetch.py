#!/usr/bin/env python3
"""Public-safe S1 helper for local trace preparation.

This script intentionally reads local files only. It can clean one trace JSON
file with the package redactor and write a small manifest skeleton.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auto_evoloop.traces.clean import clean_trace_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a local trace for S1.")
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output-trace", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--experiment-id", default="synthetic_experiment")
    args = parser.parse_args()

    clean_trace_file(args.trace, args.output_trace)
    manifest = {
        "experiment_id": args.experiment_id,
        "display_name": args.experiment_id.replace("_", " ").title(),
        "schema": {},
        "selected_cases": [],
        "trace_files": [str(args.output_trace)],
        "run_metadata": {"source": "local_trace_file"},
        "review_status": "draft",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
