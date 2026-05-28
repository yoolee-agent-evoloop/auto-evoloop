from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScoreSummary:
    total: int
    passed: int

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


def score_file(input_path: Path, output_path: Path, scorer: str = "local") -> ScoreSummary:
    if scorer == "llm":
        _raise_llm_not_implemented()
    elif scorer != "local":
        raise ValueError("scorer must be 'local' or 'llm'")

    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        base_fields = reader.fieldnames or []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = base_fields + ["ai_score", "ai_reason"]
    passed = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            score, reason = local_score(row)
            passed += int(score == 1)
            out = dict(row)
            out["ai_score"] = str(score)
            out["ai_reason"] = reason
            writer.writerow(out)

    return ScoreSummary(total=len(rows), passed=passed)


def local_score(row: dict[str, str]) -> tuple[int, str]:
    expected = row.get("expected_behavior", "")
    actual = row.get("actual_output", "")
    if not actual:
        return 0, "missing actual_output"

    required = [marker.strip().lower() for marker in expected.split(";") if marker.strip()]
    actual_lower = actual.lower()
    missing = [marker for marker in required if marker not in actual_lower]
    if missing:
        return 0, "missing expected behavior: " + ", ".join(missing)
    return 1, "all expected behavior markers found"


def _raise_llm_not_implemented() -> None:
    if os.getenv("AUTO_EVOLOOP_SCORER_API_KEY"):
        raise RuntimeError("LLM scoring is reserved for a future alpha; use --scorer local.")
    raise RuntimeError(
        "LLM scoring is reserved for a future alpha and requires "
        "AUTO_EVOLOOP_SCORER_API_KEY when implemented. Use --scorer local."
    )
