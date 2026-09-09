# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Test suite generator that combines AST analysis with testing strategies.

Orchestrates the full pipeline: analyze source -> apply strategies ->
render test code via Jinja2 templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from jinja2 import Environment, FileSystemLoader, select_autoescape

from testpilot.analyzer import analyze_module, analyze_paths
from testpilot.models import (
    AnalysisReport,
    CoverageGap,
    FunctionInfo,
    ModuleAnalysis,
    TestCase,
    TestPilotConfig,
    TestSuite,
)
from testpilot.strategies import (
    generate_basic_cases,
    generate_boundary_cases,
    generate_equivalence_cases,
    generate_mutation_hints,
)


# ---------------------------------------------------------------------------
# Template setup
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _get_jinja_env() -> Environment:
    """Create a Jinja2 environment pointing at the built-in templates."""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


# ---------------------------------------------------------------------------
# Coverage gap detection
# ---------------------------------------------------------------------------

def detect_coverage_gaps(
    analysis: ModuleAnalysis,
    existing_test_names: set[str] | None = None,
) -> list[CoverageGap]:
    """Identify functions that lack test coverage.

    Parameters
    ----------
    analysis:
        The module analysis to inspect.
    existing_test_names:
        Optional set of known test function names to check against.

    Returns
    -------
    list[CoverageGap]
        One entry per coverage gap found.
    """
    existing = existing_test_names or set()
    gaps: list[CoverageGap] = []

    all_funcs: list[FunctionInfo] = list(analysis.functions)
    for cls in analysis.classes:
        all_funcs.extend(cls.methods)

    for func in all_funcs:
        # Skip private/dunder helpers
        if func.name.startswith("_") and not func.name.startswith("__init__"):
            continue

        # Check if any test name references this function
        has_test = any(func.name in t for t in existing)

        if not has_test:
            severity = "high" if func.complexity > 3 else "medium"
            gaps.append(
                CoverageGap(
                    function_name=func.qualified_name,
                    module_path=analysis.file_path,
                    gap_type="no_tests",
                    description=f"No test found for {func.qualified_name}",
                    severity=severity,
                    suggested_tests=[
                        f"test_{func.name}_happy_path",
                        f"test_{func.name}_edge_cases",
                    ],
                )
            )

        # Complex functions deserve extra edge-case coverage
        if func.complexity > 5:
            gaps.append(
                CoverageGap(
                    function_name=func.qualified_name,
                    module_path=analysis.file_path,
                    gap_type="missing_edge_case",
                    description=(
                        f"{func.qualified_name} has complexity {func.complexity} "
                        f"and likely needs additional branch coverage"
                    ),
                    severity="high",
                    suggested_tests=[
                        f"test_{func.name}_branch_coverage",
                    ],
                )
            )

    return gaps


# ---------------------------------------------------------------------------
# Test case generation for a single function
# ---------------------------------------------------------------------------

def generate_tests_for_function(
    func: FunctionInfo,
    config: TestPilotConfig,
) -> list[TestCase]:
    """Apply all enabled strategies to generate test cases for one function.

    Parameters
    ----------
    func:
        The function to test.
    config:
        TestPilot configuration controlling which strategies to use.

    Returns
    -------
    list[TestCase]
        Combined test cases (deduplicated by name, capped by config).
    """
    cases: list[TestCase] = []

    cases.extend(generate_basic_cases(func))

    if config.boundary_analysis:
        cases.extend(generate_boundary_cases(func))

    if config.equivalence_partitioning:
        cases.extend(generate_equivalence_cases(func))

    if config.mutation_hints:
        cases.extend(generate_mutation_hints(func))

    # Deduplicate by name
    seen: set[str] = set()
    unique: list[TestCase] = []
    for c in cases:
        if c.name not in seen:
            seen.add(c.name)
            unique.append(c)

    return unique[: config.max_tests_per_function]


# ---------------------------------------------------------------------------
# Test suite rendering
# ---------------------------------------------------------------------------

def render_test_suite(suite: TestSuite) -> str:
    """Render a TestSuite into a complete Python test file.

    Parameters
    ----------
    suite:
        The test suite containing test cases and metadata.

    Returns
    -------
    str
        Complete Python source code of the test file.
    """
    env = _get_jinja_env()
    template = env.get_template("test_module.py.j2")
    code = template.render(suite=suite)
    suite.generated_code = code
    return code


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def generate_test_suite(
    analysis: ModuleAnalysis,
    config: TestPilotConfig,
) -> TestSuite:
    """Generate a complete test suite for an analyzed module.

    Parameters
    ----------
    analysis:
        Module analysis result from the analyzer.
    config:
        TestPilot configuration.

    Returns
    -------
    TestSuite
        Test suite with generated code ready to write to disk.
    """
    all_funcs: list[FunctionInfo] = list(analysis.functions)
    for cls in analysis.classes:
        all_funcs.extend(cls.methods)

    all_cases: list[TestCase] = []
    for func in all_funcs:
        if func.name.startswith("_") and func.name != "__init__":
            continue
        all_cases.extend(generate_tests_for_function(func, config))

    # Build import list
    imports: list[str] = [
        "import pytest",
        f"# Source: {analysis.file_path}",
    ]

    suite = TestSuite(
        module_name=analysis.module_name,
        source_file=analysis.file_path,
        test_cases=all_cases,
        imports=imports,
    )

    render_test_suite(suite)
    return suite


def generate_report(
    paths: Sequence[Path],
    config: TestPilotConfig,
) -> AnalysisReport:
    """Run the full pipeline: analyze files, generate tests, detect gaps.

    Parameters
    ----------
    paths:
        Python source files to process.
    config:
        TestPilot configuration.

    Returns
    -------
    AnalysisReport
        Complete report with analyses, test suites, and coverage gaps.
    """
    analyses = analyze_paths(paths)
    report = AnalysisReport(
        project_path=str(config.target_path),
        modules_analyzed=len(analyses),
        module_analyses=analyses,
    )

    for analysis in analyses:
        report.total_functions += len(analysis.functions)
        report.total_classes += len(analysis.classes)
        for cls in analysis.classes:
            report.total_functions += len(cls.methods)

        suite = generate_test_suite(analysis, config)
        report.test_suites.append(suite)
        report.total_tests_generated += len(suite.test_cases)

        gaps = detect_coverage_gaps(analysis)
        report.coverage_gaps.extend(gaps)

    return report
