from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from auto_evoloop.reporting.compare import compare_score_files
from auto_evoloop.scoring.score import score_file
from auto_evoloop.traces.clean import clean_trace_file


@dataclass(frozen=True)
class DemoResult:
    output_path: Path
    score_path: Path
    baseline_score_path: Path
    compare_path: Path
    report_path: Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = REPO_ROOT / "examples" / "synthetic_demo"


def run_demo(output_dir: Path, scorer: str = "local") -> DemoResult:
    if scorer not in {"local", "llm"}:
        raise ValueError("scorer must be 'local' or 'llm'")

    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = DEMO_ROOT / "input.csv"
    output_path = output_dir / "demo_output.csv"
    baseline_output_path = output_dir / "demo_baseline_output.csv"
    score_path = output_dir / "demo_scores.csv"
    baseline_score_path = output_dir / "demo_baseline_scores.csv"
    compare_path = output_dir / "demo_compare.md"
    report_path = output_dir / "demo_report.md"
    clean_trace_path = output_dir / "synthetic_trace.clean.json"

    rows = _read_rows(input_path)
    _write_outputs(output_path, rows, mode="candidate")
    _write_outputs(baseline_output_path, rows, mode="baseline")
    score_file(output_path, score_path, scorer=scorer)
    score_file(baseline_output_path, baseline_score_path, scorer="local")
    compare = compare_score_files(baseline_score_path, score_path, compare_path)
    clean_trace_file(DEMO_ROOT / "synthetic_trace.json", clean_trace_path)

    report_path.write_text(
        "\n".join(
            [
                "# Synthetic Demo Report",
                "",
                "This report was generated from public-safe synthetic data.",
                "",
                f"- Candidate pass rate: {compare.candidate_pass_rate:.1%}",
                f"- Baseline pass rate: {compare.baseline_pass_rate:.1%}",
                f"- Delta: {compare.delta_pass_rate:+.1%}",
                f"- Clean trace: `{clean_trace_path}`",
                "",
                "The demo shows the Auto-evoloop loop: run, score, compare, and report.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return DemoResult(output_path, score_path, baseline_score_path, compare_path, report_path)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_outputs(path: Path, rows: list[dict[str, str]], mode: str) -> None:
    fieldnames = list(rows[0].keys()) + ["actual_output"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["actual_output"] = _candidate_response(row) if mode == "candidate" else _baseline_response(row)
            writer.writerow(out)


def _candidate_response(row: dict[str, str]) -> str:
    query = row["user_query"].lower()
    if "billing" in query or "invoice" in query:
        return "I confirmed the plan, explained the monthly price, and offered to send the next billing link."
    if "upgrade" in query:
        return "I confirmed the requested upgrade, quoted the new price, and described the next step."
    if "cancel" in query:
        return "I confirmed the cancellation request, summarized the plan impact, and explained the next step."
    return "I confirmed the request, quoted the plan impact, and explained the next step."


def _baseline_response(row: dict[str, str]) -> str:
    return "I can help with that. Please check your account page."
