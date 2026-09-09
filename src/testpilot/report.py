# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Report generation for TestPilot AI analysis results.

Produces human-readable text and JSON reports summarising the analysis,
generated tests, and coverage gaps.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TextIO

from testpilot.models import AnalysisReport


def format_text_report(report: AnalysisReport) -> str:
    """Format an analysis report as a human-readable text string.

    Parameters
    ----------
    report:
        The analysis report to format.

    Returns
    -------
    str
        Multi-line text report.
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  TestPilot AI - Analysis Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Project path:      {report.project_path}")
    lines.append(f"Modules analyzed:  {report.modules_analyzed}")
    lines.append(f"Total functions:   {report.total_functions}")
    lines.append(f"Total classes:     {report.total_classes}")
    lines.append(f"Tests generated:   {report.total_tests_generated}")
    lines.append("")

    if report.coverage_gaps:
        lines.append("-" * 40)
        lines.append("  Coverage Gaps")
        lines.append("-" * 40)
        for gap in report.coverage_gaps:
            marker = {"high": "[!]", "medium": "[~]", "low": "[ ]"}.get(
                gap.severity, "[ ]"
            )
            lines.append(f"  {marker} {gap.function_name}: {gap.description}")
            if gap.suggested_tests:
                for st in gap.suggested_tests:
                    lines.append(f"        -> {st}")
        lines.append("")

    if report.module_analyses:
        lines.append("-" * 40)
        lines.append("  Module Details")
        lines.append("-" * 40)
        for mod in report.module_analyses:
            lines.append(f"  {mod.module_name} ({mod.total_lines} lines)")
            lines.append(f"    Functions: {len(mod.functions)}")
            lines.append(f"    Classes:   {len(mod.classes)}")
            if mod.parse_errors:
                for err in mod.parse_errors:
                    lines.append(f"    ERROR: {err}")
        lines.append("")

    if report.test_suites:
        lines.append("-" * 40)
        lines.append("  Generated Test Suites")
        lines.append("-" * 40)
        for suite in report.test_suites:
            lines.append(
                f"  {suite.module_name}: {len(suite.test_cases)} test cases"
            )
            for tc in suite.test_cases:
                tag = f"[{tc.strategy}]"
                lines.append(f"    {tag:12s} {tc.name}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json_report(report: AnalysisReport) -> str:
    """Format an analysis report as a JSON string.

    Parameters
    ----------
    report:
        The analysis report to format.

    Returns
    -------
    str
        Pretty-printed JSON representation.
    """
    return report.model_dump_json(indent=2)


def write_report(
    report: AnalysisReport,
    output_path: Path,
    fmt: str = "text",
) -> Path:
    """Write a report to disk.

    Parameters
    ----------
    report:
        The analysis report.
    output_path:
        Directory or file path. If a directory, a default filename is used.
    fmt:
        ``"text"`` or ``"json"``.

    Returns
    -------
    Path
        The path the report was written to.
    """
    if output_path.is_dir():
        ext = "json" if fmt == "json" else "txt"
        output_path = output_path / f"testpilot_report.{ext}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = format_json_report(report) if fmt == "json" else format_text_report(report)
    output_path.write_text(content, encoding="utf-8")
    return output_path
