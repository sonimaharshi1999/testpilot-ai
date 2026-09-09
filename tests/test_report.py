# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for report generation."""

from __future__ import annotations

import json
from pathlib import Path

from testpilot.generator import generate_report
from testpilot.models import TestPilotConfig
from testpilot.report import format_json_report, format_text_report, write_report


class TestFormatTextReport:
    """Tests for text report formatting."""

    def test_contains_header(self, calculator_path: Path) -> None:
        """Text report has the TestPilot header."""
        config = TestPilotConfig()
        report = generate_report([calculator_path], config)
        text = format_text_report(report)
        assert "TestPilot AI" in text

    def test_contains_module_details(self, calculator_path: Path) -> None:
        """Text report mentions the analyzed module."""
        config = TestPilotConfig()
        report = generate_report([calculator_path], config)
        text = format_text_report(report)
        assert "calculator" in text


class TestFormatJsonReport:
    """Tests for JSON report formatting."""

    def test_valid_json(self, calculator_path: Path) -> None:
        """JSON report is valid JSON."""
        config = TestPilotConfig()
        report = generate_report([calculator_path], config)
        raw = format_json_report(report)
        parsed = json.loads(raw)
        assert "modules_analyzed" in parsed

    def test_contains_test_suites(self, calculator_path: Path) -> None:
        """JSON report includes generated test suites."""
        config = TestPilotConfig()
        report = generate_report([calculator_path], config)
        raw = format_json_report(report)
        parsed = json.loads(raw)
        assert len(parsed["test_suites"]) > 0


class TestWriteReport:
    """Tests for writing reports to disk."""

    def test_write_text_to_directory(
        self, calculator_path: Path, tmp_path: Path
    ) -> None:
        """Writing to a directory creates a .txt file."""
        config = TestPilotConfig()
        report = generate_report([calculator_path], config)
        out = write_report(report, tmp_path, fmt="text")
        assert out.exists()
        assert out.suffix == ".txt"
        content = out.read_text(encoding="utf-8")
        assert "TestPilot AI" in content

    def test_write_json_to_directory(
        self, calculator_path: Path, tmp_path: Path
    ) -> None:
        """Writing JSON to a directory creates a .json file."""
        config = TestPilotConfig()
        report = generate_report([calculator_path], config)
        out = write_report(report, tmp_path, fmt="json")
        assert out.exists()
        assert out.suffix == ".json"
