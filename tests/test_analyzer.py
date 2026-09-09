# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for the AST analyzer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from testpilot.analyzer import (
    analyze_module,
    analyze_paths,
)
from testpilot.models import TypeCategory


class TestAnalyzeModule:
    """Tests for analyze_module()."""

    def test_basic_function_extraction(self, sample_source: Path) -> None:
        """Verify that top-level functions are extracted."""
        result = analyze_module(sample_source)
        names = [f.name for f in result.functions]
        assert "greet" in names
        assert "add" in names

    def test_function_parameters(self, sample_source: Path) -> None:
        """Verify parameter extraction including annotations."""
        result = analyze_module(sample_source)
        add_fn = next(f for f in result.functions if f.name == "add")
        param_names = [p.name for p in add_fn.parameters]
        assert "a" in param_names
        assert "b" in param_names

    def test_return_annotation(self, sample_source: Path) -> None:
        """Verify return annotation is captured."""
        result = analyze_module(sample_source)
        greet_fn = next(f for f in result.functions if f.name == "greet")
        assert greet_fn.return_annotation == "str"

    def test_type_category_inference(self, sample_source: Path) -> None:
        """Verify type categories are inferred from annotations."""
        result = analyze_module(sample_source)
        add_fn = next(f for f in result.functions if f.name == "add")
        a_param = next(p for p in add_fn.parameters if p.name == "a")
        assert a_param.type_category == TypeCategory.INTEGER

    def test_class_extraction(self, complex_source: Path) -> None:
        """Verify class and method extraction."""
        result = analyze_module(complex_source)
        assert len(result.classes) == 1
        cls = result.classes[0]
        assert cls.name == "Processor"
        method_names = [m.name for m in cls.methods]
        assert "__init__" in method_names
        assert "process" in method_names

    def test_cyclomatic_complexity(self, complex_source: Path) -> None:
        """Verify complexity calculation for branching code."""
        result = analyze_module(complex_source)
        cls = result.classes[0]
        process_method = next(m for m in cls.methods if m.name == "process")
        # if/elif/elif/else = 4 branches minimum
        assert process_method.complexity >= 4

    def test_docstring_extraction(self, sample_source: Path) -> None:
        """Verify docstrings are captured."""
        result = analyze_module(sample_source)
        greet_fn = next(f for f in result.functions if f.name == "greet")
        assert greet_fn.docstring == "Say hello."

    def test_total_lines(self, sample_source: Path) -> None:
        """Verify line count."""
        result = analyze_module(sample_source)
        assert result.total_lines > 0

    def test_syntax_error_handling(self, tmp_path: Path) -> None:
        """Verify graceful handling of syntax errors."""
        bad = tmp_path / "bad.py"
        bad.write_text("def broken(\n", encoding="utf-8")
        result = analyze_module(bad)
        assert len(result.parse_errors) > 0

    def test_calculator_sample(self, calculator_path: Path) -> None:
        """Verify analysis of the calculator sample file."""
        result = analyze_module(calculator_path)
        func_names = [f.name for f in result.functions]
        assert "add" in func_names
        assert "divide" in func_names
        assert "factorial" in func_names
        assert len(result.classes) >= 1


class TestAnalyzePaths:
    """Tests for analyze_paths()."""

    def test_multiple_files(
        self, sample_source: Path, complex_source: Path
    ) -> None:
        """Verify analyzing multiple files."""
        results = analyze_paths([sample_source, complex_source])
        assert len(results) == 2

    def test_skips_non_python(self, tmp_path: Path) -> None:
        """Verify non-.py files are skipped."""
        txt = tmp_path / "readme.txt"
        txt.write_text("not python", encoding="utf-8")
        results = analyze_paths([txt])
        assert len(results) == 0
