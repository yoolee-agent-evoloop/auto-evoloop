from __future__ import annotations

import csv
from pathlib import Path


def extract_sample_file(
    input_path: Path,
    output_path: Path,
    sessions: str | None = None,
    rows: str | None = None,
    session_turns: str | None = None,
) -> int:
    selectors = [sessions is not None, rows is not None, session_turns is not None]
    if sum(selectors) != 1:
        raise ValueError("choose exactly one selector: --sessions, --rows, or --session-turns")

    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        all_rows = list(reader)
        fieldnames = reader.fieldnames or []

    if sessions is not None:
        session_set = {item.strip() for item in sessions.split(",") if item.strip()}
        selected = [row for row in all_rows if row.get("session_number", "").strip() in session_set]
    elif rows is not None:
        row_numbers = {int(item.strip()) for item in rows.split(",") if item.strip()}
        selected = [row for index, row in enumerate(all_rows, start=1) if index in row_numbers]
    else:
        pairs = {
            tuple(item.strip() for item in pair.split(":", 1))
            for pair in (session_turns or "").split(",")
            if pair.strip()
        }
        selected = [
            row
            for row in all_rows
            if (row.get("session_number", "").strip(), row.get("turn_number", "").strip()) in pairs
        ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)
    return len(selected)
