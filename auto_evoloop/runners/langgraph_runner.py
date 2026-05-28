from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable


AgentFn = Callable[[dict[str, str]], str]


def run_eval_csv(input_path: Path, output_path: Path, agent_fn: AgentFn) -> int:
    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields + ["actual_output"])
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["actual_output"] = agent_fn(row)
            writer.writerow(out)
    return len(rows)
