from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from auto_evoloop.demo.run import run_demo
from auto_evoloop.reporting.compare import compare_score_files
from auto_evoloop.sampling.extract_sample import extract_sample_file
from auto_evoloop.scoring.score import score_file
from auto_evoloop.traces.clean import clean_trace_file

app = typer.Typer(help="Auto-evoloop agent evaluation and optimization toolkit.")
demo_app = typer.Typer(help="Run public-safe synthetic demos.")
sample_app = typer.Typer(help="Extract evaluation samples.")
trace_app = typer.Typer(help="Clean or normalize trace data.")


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", help="Show package version and exit."),
) -> None:
    if version:
        from auto_evoloop import __version__

        typer.echo(__version__)
        raise typer.Exit()


@demo_app.command("run")
def demo_run(
    output_dir: Path = typer.Option(
        Path("/tmp/auto-evoloop-demo"),
        "--output-dir",
        help="Directory for generated demo artifacts.",
    ),
    scorer: str = typer.Option("local", "--scorer", help="Scorer to use: local or reserved llm hook."),
) -> None:
    try:
        result = run_demo(output_dir=output_dir, scorer=scorer)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Demo completed: {result.report_path}")


@sample_app.command("extract")
def sample_extract(
    input: Path = typer.Option(..., "--input", "-i", help="Input CSV."),
    output: Path = typer.Option(..., "--output", "-o", help="Output CSV."),
    sessions: Optional[str] = typer.Option(None, "--sessions", help="Comma-separated session ids."),
    rows: Optional[str] = typer.Option(None, "--rows", help="Comma-separated 1-based row numbers."),
    session_turns: Optional[str] = typer.Option(
        None,
        "--session-turns",
        help="Comma-separated session:turn pairs.",
    ),
) -> None:
    try:
        count = extract_sample_file(
            input_path=input,
            output_path=output,
            sessions=sessions,
            rows=rows,
            session_turns=session_turns,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote {count} rows to {output}")


@app.command("score")
def score(
    input: Path = typer.Option(..., "--input", "-i", help="Agent output CSV."),
    output: Path = typer.Option(..., "--output", "-o", help="Scored output CSV."),
    scorer: str = typer.Option("local", "--scorer", help="Scorer to use: local or reserved llm hook."),
) -> None:
    try:
        summary = score_file(input_path=input, output_path=output, scorer=scorer)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Scored {summary.total} rows: pass_rate={summary.pass_rate:.1%}")


@app.command("compare")
def compare(
    baseline: Path = typer.Option(..., "--baseline", help="Baseline scored CSV."),
    candidate: Path = typer.Option(..., "--candidate", help="Candidate scored CSV."),
    output: Path = typer.Option(..., "--output", "-o", help="Markdown comparison output."),
) -> None:
    summary = compare_score_files(baseline_path=baseline, candidate_path=candidate, output_path=output)
    typer.echo(f"Comparison written: {output} (delta={summary.delta_pass_rate:+.1%})")


@trace_app.command("clean")
def trace_clean(
    input: Path = typer.Option(..., "--input", "-i", help="Trace JSON input."),
    output: Path = typer.Option(..., "--output", "-o", help="Clean JSON output."),
) -> None:
    clean_trace_file(input_path=input, output_path=output)
    typer.echo(f"Clean trace written: {output}")


app.add_typer(demo_app, name="demo")
app.add_typer(sample_app, name="sample")
app.add_typer(trace_app, name="trace")
