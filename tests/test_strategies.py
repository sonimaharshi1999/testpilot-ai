# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for test generation strategies."""

from __future__ import annotations

from testpilot.models import FunctionInfo, ParameterInfo, TypeCategory
from testpilot.strategies import (
    generate_basic_cases,
    generate_boundary_cases,
    generate_equivalence_cases,
    generate_mutation_hints,
)


def _make_func(
    name: str = "example",
    params: list[ParameterInfo] | None = None,
    complexity: int = 1,
) -> FunctionInfo:
    """Helper to create a FunctionInfo for tests."""
    return FunctionInfo(
        name=name,
        module_path="test_module",
        lineno=1,
        parameters=params or [],
        complexity=complexity,
    )


class TestBoundaryAnalysis:
    """Tests for boundary value analysis strategy."""

    def test_integer_boundaries(self) -> None:
        """Boundary values generated for int params."""
        func = _make_func(
            params=[
                ParameterInfo(
                    name="n",
                    annotation="int",
                    type_category=TypeCategory.INTEGER,
                )
            ]
        )
        cases = generate_boundary_cases(func)
        assert len(cases) > 0
        assert all(c.strategy == "boundary" for c in cases)
        assert all(c.is_edge_case for c in cases)

    def test_string_boundaries(self) -> None:
        """Boundary values generated for str params."""
        func = _make_func(
            params=[
                ParameterInfo(
                    name="text",
                    annotation="str",
                    type_category=TypeCategory.STRING,
                )
            ]
        )
        cases = generate_boundary_cases(func)
        assert len(cases) > 0
        # Should include empty string
        descriptions = " ".join(c.description for c in cases)
        assert "boundary" in descriptions.lower()

    def test_optional_param_includes_none(self) -> None:
        """Optional params should have None as a boundary value."""
        func = _make_func(
            params=[
                ParameterInfo(
                    name="val",
                    annotation="Optional[int]",
                    type_category=TypeCategory.OPTIONAL,
                    is_optional=True,
                )
            ]
        )
        cases = generate_boundary_cases(func)
        inputs = [c.inputs.get("val") for c in cases]
        assert "None" in inputs

    def test_self_param_excluded(self) -> None:
        """The 'self' parameter should not generate boundary tests."""
        func = _make_func(
            params=[
                ParameterInfo(name="self"),
                ParameterInfo(
                    name="x",
                    annotation="int",
                    type_category=TypeCategory.INTEGER,
                ),
            ]
        )
        cases = generate_boundary_cases(func)
        param_names = set()
        for c in cases:
            param_names.update(c.inputs.keys())
        assert "self" not in param_names


class TestEquivalencePartitioning:
    """Tests for equivalence partitioning strategy."""

    def test_integer_partitions(self) -> None:
        """Equivalence classes generated for int params."""
        func = _make_func(
            params=[
                ParameterInfo(
                    name="count",
                    annotation="int",
                    type_category=TypeCategory.INTEGER,
                )
            ]
        )
        cases = generate_equivalence_cases(func)
        assert len(cases) >= 3  # negative, zero, positive
        labels = [c.name for c in cases]
        assert any("negative" in l for l in labels)
        assert any("zero" in l for l in labels)
        assert any("positive" in l for l in labels)

    def test_string_partitions(self) -> None:
        """Equivalence classes for string params."""
        func = _make_func(
            params=[
                ParameterInfo(
                    name="text",
                    annotation="str",
                    type_category=TypeCategory.STRING,
                )
            ]
        )
        cases = generate_equivalence_cases(func)
        assert len(cases) >= 3


class TestMutationHints:
    """Tests for mutation testing hint strategy."""

    def test_no_hints_for_simple_functions(self) -> None:
        """Low-complexity functions get no mutation hints."""
        func = _make_func(complexity=1)
        cases = generate_mutation_hints(func)
        assert len(cases) == 0

    def test_hints_for_complex_functions(self) -> None:
        """Complex functions get mutation hints."""
        func = _make_func(complexity=5)
        cases = generate_mutation_hints(func)
        assert len(cases) > 0
        assert all(c.strategy == "mutation" for c in cases)


class TestBasicCases:
    """Tests for basic happy-path / error-path generation."""

    def test_happy_path_always_generated(self) -> None:
        """A happy path test is always generated."""
        func = _make_func()
        cases = generate_basic_cases(func)
        assert any("happy_path" in c.name for c in cases)

    def test_none_input_for_required_params(self) -> None:
        """Error path with None is generated when required params exist."""
        func = _make_func(
            params=[
                ParameterInfo(
                    name="x",
                    annotation="int",
                    type_category=TypeCategory.INTEGER,
                )
            ]
        )
        cases = generate_basic_cases(func)
        assert any("none_input" in c.name for c in cases)
