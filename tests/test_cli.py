from pathlib import Path

from typer.testing import CliRunner

from auto_evoloop.cli import app


runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Auto-evoloop" in result.output


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0a2" in result.output


def test_demo_run(tmp_path: Path) -> None:
    result = runner.invoke(app, ["demo", "run", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "demo_output.csv").exists()
    assert (tmp_path / "demo_scores.csv").exists()
    assert (tmp_path / "demo_compare.md").exists()
    assert (tmp_path / "demo_report.md").exists()


def test_demo_llm_hook_is_friendly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["demo", "run", "--output-dir", str(tmp_path), "--scorer", "llm"])
    assert result.exit_code != 0
    assert "LLM scoring is reserved" in result.output


def test_invalid_scorer_is_friendly(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "score",
            "--input",
            "examples/synthetic_demo/input.csv",
            "--output",
            str(tmp_path / "scores.csv"),
            "--scorer",
            "unknown",
        ],
    )
    assert result.exit_code != 0
    assert "scorer must be" in result.output


def test_sample_extract(tmp_path: Path) -> None:
    output = tmp_path / "sample.csv"
    result = runner.invoke(
        app,
        [
            "sample",
            "extract",
            "--input",
            "examples/synthetic_demo/input.csv",
            "--output",
            str(output),
            "--sessions",
            "1,3",
        ],
    )
    assert result.exit_code == 0
    assert output.read_text(encoding="utf-8").count("\n") == 3


def test_sample_extract_rejects_multiple_selectors(tmp_path: Path) -> None:
    output = tmp_path / "sample.csv"
    result = runner.invoke(
        app,
        [
            "sample",
            "extract",
            "--input",
            "examples/synthetic_demo/input.csv",
            "--output",
            str(output),
            "--sessions",
            "1",
            "--rows",
            "1",
        ],
    )
    assert result.exit_code != 0
    assert "choose exactly one selector" in result.output


def test_score_and_compare_commands(tmp_path: Path) -> None:
    demo_result = runner.invoke(app, ["demo", "run", "--output-dir", str(tmp_path)])
    assert demo_result.exit_code == 0

    score_output = tmp_path / "manual_scores.csv"
    score_result = runner.invoke(
        app,
        [
            "score",
            "--input",
            str(tmp_path / "demo_output.csv"),
            "--output",
            str(score_output),
        ],
    )
    assert score_result.exit_code == 0
    assert "pass_rate=100.0%" in score_result.output

    compare_output = tmp_path / "manual_compare.md"
    compare_result = runner.invoke(
        app,
        [
            "compare",
            "--baseline",
            str(tmp_path / "demo_baseline_scores.csv"),
            "--candidate",
            str(score_output),
            "--output",
            str(compare_output),
        ],
    )
    assert compare_result.exit_code == 0
    assert "delta=+100.0%" in compare_result.output


def test_trace_clean(tmp_path: Path) -> None:
    output = tmp_path / "trace.clean.json"
    result = runner.invoke(
        app,
        [
            "trace",
            "clean",
            "--input",
            "examples/synthetic_demo/synthetic_trace.json",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    assert "[REDACTED]" in output.read_text(encoding="utf-8")
