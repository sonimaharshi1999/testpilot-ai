# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for Pydantic models."""

from __future__ import annotations

from pathlib import Path

from testpilot.models import (
    AnalysisReport,
    CoverageGap,
    FunctionInfo,
    ModuleAnalysis,
    ParameterInfo,
    TestCase,
    TestPilotConfig,
    TestSuite,
    TypeCategory,
)


class TestFunctionInfo:
    """Tests for FunctionInfo model."""

    def test_qualified_name_standalone(self) -> None:
        """Standalone function returns just its name."""
        func = FunctionInfo(name="foo", module_path="mod", lineno=1)
        assert func.qualified_name == "foo"

    def test_qualified_name_method(self) -> None:
        """Method returns Class.method."""
        func = FunctionInfo(
            name="bar", module_path="mod", lineno=1, class_name="MyClass"
        )
        assert func.qualified_name == "MyClass.bar"


class TestParameterInfo:
    """Tests for ParameterInfo model."""

    def test_defaults(self) -> None:
        """Default values are sensible."""
        p = ParameterInfo(name="x")
        assert p.annotation is None
        assert p.default is None
        assert p.type_category == TypeCategory.UNKNOWN
        assert p.is_optional is False


class TestTestPilotConfig:
    """Tests for configuration model."""

    def test_defaults(self) -> None:
        """Default config has sensible values."""
        cfg = TestPilotConfig()
        assert cfg.llm_provider == "none"
        assert cfg.max_tests_per_function == 8
        assert cfg.boundary_analysis is True
        assert cfg.equivalence_partitioning is True
        assert cfg.mutation_hints is True

    def test_custom_config(self) -> None:
        """Custom values override defaults."""
        cfg = TestPilotConfig(
            max_tests_per_function=3,
            boundary_analysis=False,
        )
        assert cfg.max_tests_per_function == 3
        assert cfg.boundary_analysis is False


class TestTestCase:
    """Tests for TestCase model."""

    def test_serialization(self) -> None:
        """TestCase round-trips through dict."""
        tc = TestCase(
            name="test_foo",
            function_under_test="foo",
            inputs={"x": "42"},
            strategy="boundary",
        )
        data = tc.model_dump()
        restored = TestCase(**data)
        assert restored.name == "test_foo"
        assert restored.inputs == {"x": "42"}


class TestAnalysisReport:
    """Tests for AnalysisReport model."""

    def test_empty_report(self) -> None:
        """An empty report has zero counts."""
        report = AnalysisReport(project_path="/tmp")
        assert report.modules_analyzed == 0
        assert report.total_functions == 0
        assert report.total_tests_generated == 0
