# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Click-based CLI for TestPilot AI.

Commands
--------
- ``testpilot generate <path>`` -- generate tests for Python source files
- ``testpilot analyze <path>``  -- analyze source and print structure
- ``testpilot report <path>``   -- produce a full analysis report
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from testpilot.__version__ import __version__
from testpilot.analyzer import analyze_module, analyze_paths
from testpilot.generator import generate_report, generate_test_suite
from testpilot.models import TestPilotConfig
from testpilot.report import format_text_report, write_report


def _collect_py_files(target: Path, config: TestPilotConfig) -> list[Path]:
    """Gather Python files from a path, respecting excludes.

    Parameters
    ----------
    target:
        File or directory to scan.
    config:
        Configuration with include/exclude patterns.

    Returns
    -------
    list[Path]
        Matching Python files.
    """
    if target.is_file():
        return [target]

    files: list[Path] = []
    for pattern in config.include_patterns:
        # rglob already searches recursively, so strip the leading **/ prefix
        clean = pattern.removeprefix("**/")
        for p in target.rglob(clean):
            skip = False
            for exc in config.exclude_patterns:
                exc_clean = exc.removeprefix("**/")
                if p.match(exc_clean):
                    skip = True
                    break
            if not skip and p.is_file():
                files.append(p)
    return sorted(set(files))


@click.group()
@click.version_option(version=__version__, prog_name="testpilot")
def main() -> None:
    """TestPilot AI - Intelligent Test Generation Framework."""


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="tests/generated",
    help="Output directory for generated tests.",
)
@click.option(
    "--provider",
    type=click.Choice(["none", "claude_cli", "api"]),
    default="none",
    help="LLM provider for enhanced generation.",
)
@click.option("--no-boundary", is_flag=True, help="Disable boundary analysis.")
@click.option("--no-equivalence", is_flag=True, help="Disable equivalence partitioning.")
@click.option("--no-mutation", is_flag=True, help="Disable mutation hints.")
@click.option("--max-tests", type=int, default=8, help="Max tests per function.")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
def generate(
    path: str,
    output: str,
    provider: str,
    no_boundary: bool,
    no_equivalence: bool,
    no_mutation: bool,
    max_tests: int,
    verbose: bool,
) -> None:
    """Generate test suites for Python source files at PATH."""
    target = Path(path)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = TestPilotConfig(
        target_path=target,
        output_dir=output_dir,
        llm_provider=provider,
        boundary_analysis=not no_boundary,
        equivalence_partitioning=not no_equivalence,
        mutation_hints=not no_mutation,
        max_tests_per_function=max_tests,
        verbose=verbose,
    )

    py_files = _collect_py_files(target, config)
    if not py_files:
        click.echo("No Python files found.", err=True)
        sys.exit(1)

    click.echo(f"Analyzing {len(py_files)} file(s)...")

    total_tests = 0
    for src_file in py_files:
        analysis = analyze_module(src_file)
        suite = generate_test_suite(analysis, config)

        if suite.generated_code:
            out_file = output_dir / f"test_{src_file.stem}_generated.py"
            out_file.write_text(suite.generated_code, encoding="utf-8")
            total_tests += len(suite.test_cases)
            if verbose:
                click.echo(
                    f"  {src_file.name} -> {out_file.name} "
                    f"({len(suite.test_cases)} tests)"
                )

    click.echo(f"Generated {total_tests} test(s) in {output_dir}/")


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Show full details.")
def analyze(path: str, verbose: bool) -> None:
    """Analyze Python source code at PATH and print structure."""
    target = Path(path)
    config = TestPilotConfig(target_path=target, verbose=verbose)
    py_files = _collect_py_files(target, config)

    if not py_files:
        click.echo("No Python files found.", err=True)
        sys.exit(1)

    analyses = analyze_paths(py_files)

    for mod in analyses:
        click.echo(f"\n{'=' * 50}")
        click.echo(f"Module: {mod.module_name} ({mod.total_lines} lines)")
        click.echo(f"File:   {mod.file_path}")

        if mod.parse_errors:
            for err in mod.parse_errors:
                click.echo(f"  ERROR: {err}")
            continue

        for func in mod.functions:
            params = ", ".join(
                f"{p.name}: {p.annotation or '?'}" for p in func.parameters
            )
            ret = func.return_annotation or "?"
            click.echo(f"  def {func.name}({params}) -> {ret}  [complexity={func.complexity}]")

        for cls in mod.classes:
            click.echo(f"  class {cls.name}({', '.join(cls.bases) or 'object'}):")
            for m in cls.methods:
                params = ", ".join(
                    f"{p.name}: {p.annotation or '?'}" for p in m.parameters
                )
                click.echo(f"    def {m.name}({params})")

    click.echo(f"\nAnalyzed {len(analyses)} module(s).")


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default=None,
    help="Output file or directory for the report.",
)
@click.option(
    "--format", "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Report format.",
)
def report(path: str, output: Optional[str], fmt: str) -> None:
    """Generate a full analysis report for PATH."""
    target = Path(path)
    config = TestPilotConfig(target_path=target)
    py_files = _collect_py_files(target, config)

    if not py_files:
        click.echo("No Python files found.", err=True)
        sys.exit(1)

    click.echo(f"Analyzing {len(py_files)} file(s)...")
    analysis_report = generate_report(py_files, config)

    if output:
        out_path = write_report(analysis_report, Path(output), fmt=fmt)
        click.echo(f"Report written to {out_path}")
    else:
        click.echo(format_text_report(analysis_report))


if __name__ == "__main__":
    main()
