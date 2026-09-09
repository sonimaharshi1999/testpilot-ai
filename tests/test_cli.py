# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for the Click CLI."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from testpilot.cli import main


class TestCLIGenerate:
    """Tests for the 'generate' command."""

    def test_generate_creates_files(
        self, calculator_path: Path, tmp_path: Path
    ) -> None:
        """'generate' command creates test files."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["generate", str(calculator_path), "-o", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "Generated" in result.output
        generated = list(tmp_path.glob("test_*_generated.py"))
        assert len(generated) >= 1

    def test_generate_verbose(
        self, calculator_path: Path, tmp_path: Path
    ) -> None:
        """Verbose flag prints per-file info."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["generate", str(calculator_path), "-o", str(tmp_path), "-v"],
        )
        assert result.exit_code == 0
        assert "calculator" in result.output


class TestCLIAnalyze:
    """Tests for the 'analyze' command."""

    def test_analyze_prints_functions(self, calculator_path: Path) -> None:
        """'analyze' lists functions in output."""
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", str(calculator_path)])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "divide" in result.output

    def test_analyze_directory(self, calculator_path: Path) -> None:
        """'analyze' works on a directory."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["analyze", str(calculator_path.parent)]
        )
        assert result.exit_code == 0
        assert "Analyzed" in result.output


class TestCLIReport:
    """Tests for the 'report' command."""

    def test_report_stdout(self, calculator_path: Path) -> None:
        """'report' prints to stdout when no -o given."""
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(calculator_path)])
        assert result.exit_code == 0
        assert "TestPilot AI" in result.output

    def test_report_json_output(
        self, calculator_path: Path, tmp_path: Path
    ) -> None:
        """'report --format json -o DIR' writes a JSON file."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "report",
                str(calculator_path),
                "--format",
                "json",
                "-o",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "Report written" in result.output


class TestCLIVersion:
    """Test --version flag."""

    def test_version_flag(self) -> None:
        """'--version' prints version info."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "testpilot" in result.output
