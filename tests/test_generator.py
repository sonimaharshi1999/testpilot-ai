# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for the test generator pipeline."""

from __future__ import annotations

from pathlib import Path

from testpilot.analyzer import analyze_module
from testpilot.generator import (
    detect_coverage_gaps,
    generate_report,
    generate_test_suite,
    generate_tests_for_function,
    render_test_suite,
)
from testpilot.models import TestPilotConfig, TestSuite


class TestGenerateTestsForFunction:
    """Tests for per-function test generation."""

    def test_generates_cases(self, sample_source: Path) -> None:
        """At least one test case is generated for each function."""
        analysis = analyze_module(sample_source)
        config = TestPilotConfig()
        for func in analysis.functions:
            cases = generate_tests_for_function(func, config)
            assert len(cases) > 0, f"No cases for {func.name}"

    def test_respects_max_tests(self, sample_source: Path) -> None:
        """Generated cases do not exceed max_tests_per_function."""
        analysis = analyze_module(sample_source)
        config = TestPilotConfig(max_tests_per_function=3)
        for func in analysis.functions:
            cases = generate_tests_for_function(func, config)
            assert len(cases) <= 3

    def test_disabling_strategies(self, sample_source: Path) -> None:
        """Disabling all strategies still produces basic cases."""
        analysis = analyze_module(sample_source)
        config = TestPilotConfig(
            boundary_analysis=False,
            equivalence_partitioning=False,
            mutation_hints=False,
        )
        for func in analysis.functions:
            cases = generate_tests_for_function(func, config)
            # Basic strategy always generates at least a happy-path
            assert len(cases) >= 1


class TestGenerateTestSuite:
    """Tests for full suite generation."""

    def test_suite_has_code(self, calculator_path: Path) -> None:
        """Generated suite contains renderable code."""
        analysis = analyze_module(calculator_path)
        config = TestPilotConfig()
        suite = generate_test_suite(analysis, config)
        assert suite.generated_code
        assert "def test_" in suite.generated_code

    def test_suite_module_name(self, calculator_path: Path) -> None:
        """Suite captures the correct module name."""
        analysis = analyze_module(calculator_path)
        config = TestPilotConfig()
        suite = generate_test_suite(analysis, config)
        assert suite.module_name == "calculator"


class TestCoverageGaps:
    """Tests for coverage gap detection."""

    def test_detects_missing_tests(self, calculator_path: Path) -> None:
        """Functions without tests show up as coverage gaps."""
        analysis = analyze_module(calculator_path)
        gaps = detect_coverage_gaps(analysis, existing_test_names=set())
        assert len(gaps) > 0
        gap_names = [g.function_name for g in gaps]
        assert "add" in gap_names

    def test_no_gaps_when_tests_exist(self, sample_source: Path) -> None:
        """No gaps reported when all functions have tests."""
        analysis = analyze_module(sample_source)
        # Pretend we have tests for all functions
        test_names = {f"test_{f.name}" for f in analysis.functions}
        gaps = detect_coverage_gaps(analysis, existing_test_names=test_names)
        # Gaps that are "no_tests" type should be absent
        no_test_gaps = [g for g in gaps if g.gap_type == "no_tests"]
        assert len(no_test_gaps) == 0


class TestRenderTestSuite:
    """Tests for Jinja2 template rendering."""

    def test_renders_valid_python(self, calculator_path: Path) -> None:
        """Rendered code should be parseable Python."""
        import ast as stdlib_ast

        analysis = analyze_module(calculator_path)
        config = TestPilotConfig()
        suite = generate_test_suite(analysis, config)
        # Should not raise SyntaxError
        stdlib_ast.parse(suite.generated_code)


class TestGenerateReport:
    """Tests for the full report pipeline."""

    def test_report_structure(self, calculator_path: Path) -> None:
        """Report has all expected fields populated."""
        config = TestPilotConfig()
        report = generate_report([calculator_path], config)
        assert report.modules_analyzed == 1
        assert report.total_functions > 0
        assert report.total_tests_generated > 0
        assert len(report.test_suites) == 1
