# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Pydantic models for TestPilot AI code analysis and test generation."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TypeCategory(str, enum.Enum):
    """Broad category for a parameter's inferred type."""

    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    SET = "set"
    TUPLE = "tuple"
    NONE = "none"
    OPTIONAL = "optional"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class ParameterInfo(BaseModel):
    """Describes a single function parameter."""

    name: str
    annotation: str | None = None
    default: str | None = None
    type_category: TypeCategory = TypeCategory.UNKNOWN
    is_optional: bool = False


class FunctionInfo(BaseModel):
    """Describes a single function extracted from AST analysis."""

    name: str
    module_path: str
    lineno: int
    end_lineno: int | None = None
    docstring: str | None = None
    parameters: list[ParameterInfo] = Field(default_factory=list)
    return_annotation: str | None = None
    decorators: list[str] = Field(default_factory=list)
    is_method: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_property: bool = False
    class_name: str | None = None
    source_code: str = ""
    complexity: int = 1

    @property
    def qualified_name(self) -> str:
        """Return fully qualified name including class if applicable."""
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name


class ClassInfo(BaseModel):
    """Describes a class extracted from AST analysis."""

    name: str
    module_path: str
    lineno: int
    end_lineno: int | None = None
    docstring: str | None = None
    bases: list[str] = Field(default_factory=list)
    methods: list[FunctionInfo] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)


class ModuleAnalysis(BaseModel):
    """Complete analysis result for a single Python module."""

    file_path: str
    module_name: str
    functions: list[FunctionInfo] = Field(default_factory=list)
    classes: list[ClassInfo] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    total_lines: int = 0
    parse_errors: list[str] = Field(default_factory=list)


class TestCase(BaseModel):
    """A single generated test case."""

    name: str
    function_under_test: str
    description: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected_behavior: str = ""
    strategy: str = "basic"
    code: str = ""
    is_edge_case: bool = False


class TestSuite(BaseModel):
    """A collection of test cases for a module."""

    module_name: str
    source_file: str
    test_cases: list[TestCase] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    fixtures: list[str] = Field(default_factory=list)
    generated_code: str = ""


class CoverageGap(BaseModel):
    """Identifies a gap in test coverage."""

    function_name: str
    module_path: str
    gap_type: str  # e.g. "no_tests", "missing_edge_case", "uncovered_branch"
    description: str
    severity: str = "medium"  # low, medium, high
    suggested_tests: list[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    """Full report from analyzing a codebase."""

    project_path: str
    modules_analyzed: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_tests_generated: int = 0
    coverage_gaps: list[CoverageGap] = Field(default_factory=list)
    module_analyses: list[ModuleAnalysis] = Field(default_factory=list)
    test_suites: list[TestSuite] = Field(default_factory=list)


class TestPilotConfig(BaseModel):
    """Configuration for TestPilot AI."""

    target_path: Path = Path(".")
    output_dir: Path = Path("tests/generated")
    llm_provider: str = "none"
    llm_model: str = "claude-sonnet-4-20250514"
    include_patterns: list[str] = Field(default_factory=lambda: ["**/*.py"])
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["**/test_*", "**/*_test.py", "**/conftest.py", "**/__pycache__/**"]
    )
    max_tests_per_function: int = 8
    boundary_analysis: bool = True
    equivalence_partitioning: bool = True
    mutation_hints: bool = True
    verbose: bool = False
