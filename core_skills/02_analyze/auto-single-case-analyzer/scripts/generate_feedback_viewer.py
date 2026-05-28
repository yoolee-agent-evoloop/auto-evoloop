#!/usr/bin/env python3
"""Generate a small local HTML viewer for public-safe feedback JSON."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate feedback viewer HTML.")
    parser.add_argument("--feedback", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.feedback.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else [data]
    body = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('case_id', '')))}</td>"
        f"<td>{html.escape(str(row.get('failure_mode', '')))}</td>"
        f"<td>{html.escape(str(row.get('confidence', '')))}</td>"
        f"<td>{html.escape(str(row.get('finding', '')))}</td>"
        "</tr>"
        for row in rows
    )
    document = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Auto-evoloop Feedback Viewer</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #d0d7de; padding: .5rem; text-align: left; }}
th {{ background: #f6f8fa; }}
</style>
<h1>Auto-evoloop Feedback Viewer</h1>
<table>
<thead><tr><th>Case</th><th>Failure Mode</th><th>Confidence</th><th>Finding</th></tr></thead>
<tbody>
{body}
</tbody>
</table>
</html>
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8")


if __name__ == "__main__":
    main()
