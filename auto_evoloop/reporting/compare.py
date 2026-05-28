from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompareSummary:
    baseline_total: int
    baseline_passed: int
    candidate_total: int
    candidate_passed: int

    @property
    def baseline_pass_rate(self) -> float:
        return self.baseline_passed / self.baseline_total if self.baseline_total else 0.0

    @property
    def candidate_pass_rate(self) -> float:
        return self.candidate_passed / self.candidate_total if self.candidate_total else 0.0

    @property
    def delta_pass_rate(self) -> float:
        return self.candidate_pass_rate - self.baseline_pass_rate


def compare_score_files(baseline_path: Path, candidate_path: Path, output_path: Path) -> CompareSummary:
    baseline_total, baseline_passed = _read_score_counts(baseline_path)
    candidate_total, candidate_passed = _read_score_counts(candidate_path)
    summary = CompareSummary(baseline_total, baseline_passed, candidate_total, candidate_passed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_markdown(summary), encoding="utf-8")
    return summary


def _read_score_counts(path: Path) -> tuple[int, int]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    passed = sum(1 for row in rows if str(row.get("ai_score", "")).strip() == "1")
    return len(rows), passed


def _render_markdown(summary: CompareSummary) -> str:
    return "\n".join(
        [
            "# Auto-evoloop Comparison",
            "",
            "| Metric | Baseline | Candidate |",
            "| --- | ---: | ---: |",
            f"| Rows | {summary.baseline_total} | {summary.candidate_total} |",
            f"| Passed | {summary.baseline_passed} | {summary.candidate_passed} |",
            f"| Pass rate | {summary.baseline_pass_rate:.1%} | {summary.candidate_pass_rate:.1%} |",
            "",
            f"Delta pass rate: **{summary.delta_pass_rate:+.1%}**",
            "",
        ]
    )
