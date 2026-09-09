# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Test generation strategies: boundary values, equivalence partitioning,
mutation detection hints.

Each strategy inspects a FunctionInfo and produces TestCase objects that
exercise the function from a particular testing perspective.
"""

from __future__ import annotations

from typing import Any

from testpilot.models import (
    FunctionInfo,
    ParameterInfo,
    TestCase,
    TypeCategory,
)


# ---------------------------------------------------------------------------
# Boundary value analysis
# ---------------------------------------------------------------------------

_BOUNDARY_VALUES: dict[TypeCategory, list[Any]] = {
    TypeCategory.INTEGER: [0, 1, -1, 2**31 - 1, -(2**31)],
    TypeCategory.FLOAT: [0.0, 1.0, -1.0, float("inf"), float("-inf"), 1e-10],
    TypeCategory.STRING: ["", "a", " ", "a" * 256],
    TypeCategory.BOOLEAN: [True, False],
    TypeCategory.LIST: [[], [1], list(range(100))],
    TypeCategory.DICT: [{}, {"k": "v"}],
    TypeCategory.SET: [set(), {1}],
    TypeCategory.TUPLE: [(), (1,)],
}


def _boundary_values_for(param: ParameterInfo) -> list[Any]:
    """Return boundary test values appropriate for the parameter type."""
    values = _BOUNDARY_VALUES.get(param.type_category, [])
    if param.is_optional:
        values = [None, *values]
    return values


def generate_boundary_cases(func: FunctionInfo) -> list[TestCase]:
    """Generate test cases using boundary value analysis.

    For each typed parameter, picks known-tricky values at the edges
    of the domain (zero, empty, max-int, etc.).

    Parameters
    ----------
    func:
        The function to generate boundary tests for.

    Returns
    -------
    list[TestCase]
        One test case per boundary value per parameter.
    """
    cases: list[TestCase] = []
    testable = [p for p in func.parameters if p.name != "self"]

    for param in testable:
        for idx, val in enumerate(_boundary_values_for(param)):
            case_name = (
                f"test_{func.name}_boundary_{param.name}_{idx}"
            )
            cases.append(
                TestCase(
                    name=case_name,
                    function_under_test=func.qualified_name,
                    description=(
                        f"Boundary value analysis for parameter '{param.name}' "
                        f"with value {val!r}"
                    ),
                    inputs={param.name: repr(val)},
                    expected_behavior="Should not raise an unhandled exception",
                    strategy="boundary",
                    is_edge_case=True,
                )
            )
    return cases


# ---------------------------------------------------------------------------
# Equivalence partitioning
# ---------------------------------------------------------------------------

_EQUIVALENCE_CLASSES: dict[TypeCategory, list[dict[str, Any]]] = {
    TypeCategory.INTEGER: [
        {"label": "negative", "value": -5},
        {"label": "zero", "value": 0},
        {"label": "positive", "value": 42},
    ],
    TypeCategory.FLOAT: [
        {"label": "negative", "value": -3.14},
        {"label": "zero", "value": 0.0},
        {"label": "positive", "value": 2.718},
    ],
    TypeCategory.STRING: [
        {"label": "empty", "value": ""},
        {"label": "single_char", "value": "x"},
        {"label": "multi_word", "value": "hello world"},
        {"label": "numeric_string", "value": "12345"},
    ],
    TypeCategory.BOOLEAN: [
        {"label": "true", "value": True},
        {"label": "false", "value": False},
    ],
    TypeCategory.LIST: [
        {"label": "empty", "value": []},
        {"label": "single", "value": [1]},
        {"label": "multiple", "value": [1, 2, 3]},
    ],
}


def generate_equivalence_cases(func: FunctionInfo) -> list[TestCase]:
    """Generate test cases via equivalence partitioning.

    Divides each parameter's domain into representative classes and
    picks one value from each class.

    Parameters
    ----------
    func:
        The function to generate equivalence-class tests for.

    Returns
    -------
    list[TestCase]
        One test case per equivalence class per parameter.
    """
    cases: list[TestCase] = []
    testable = [p for p in func.parameters if p.name != "self"]

    for param in testable:
        classes = _EQUIVALENCE_CLASSES.get(param.type_category, [])
        for cls in classes:
            case_name = (
                f"test_{func.name}_equiv_{param.name}_{cls['label']}"
            )
            cases.append(
                TestCase(
                    name=case_name,
                    function_under_test=func.qualified_name,
                    description=(
                        f"Equivalence class '{cls['label']}' for parameter "
                        f"'{param.name}'"
                    ),
                    inputs={param.name: repr(cls["value"])},
                    expected_behavior="Returns a valid result for this class",
                    strategy="equivalence",
                )
            )
    return cases


# ---------------------------------------------------------------------------
# Mutation testing hints
# ---------------------------------------------------------------------------

_MUTATION_OPERATORS: list[dict[str, str]] = [
    {"name": "negate_condition", "description": "Negate an if-condition"},
    {"name": "off_by_one", "description": "Change < to <= or > to >="},
    {"name": "swap_operator", "description": "Swap + with - or * with /"},
    {"name": "remove_else", "description": "Remove else branch"},
    {"name": "boundary_shift", "description": "Shift boundary constant by 1"},
]


def generate_mutation_hints(func: FunctionInfo) -> list[TestCase]:
    """Generate test cases that would catch common mutations.

    Rather than actually mutating the code, this produces tests whose
    assertions are designed to fail if a typical mutation operator were
    applied to the source (condition negation, off-by-one, etc.).

    Parameters
    ----------
    func:
        The function to generate mutation-catching tests for.

    Returns
    -------
    list[TestCase]
        Test cases targeting likely mutation sites.
    """
    cases: list[TestCase] = []

    if func.complexity <= 1:
        return cases

    for op in _MUTATION_OPERATORS:
        case_name = f"test_{func.name}_mutation_{op['name']}"
        cases.append(
            TestCase(
                name=case_name,
                function_under_test=func.qualified_name,
                description=(
                    f"Mutation hint: {op['description']}. "
                    f"Complexity={func.complexity} suggests branches to test."
                ),
                expected_behavior=f"Should detect mutation: {op['name']}",
                strategy="mutation",
            )
        )
    return cases


# ---------------------------------------------------------------------------
# Basic happy-path and error-path tests
# ---------------------------------------------------------------------------

def generate_basic_cases(func: FunctionInfo) -> list[TestCase]:
    """Generate a basic happy-path test and an error-path test.

    Parameters
    ----------
    func:
        The function to create basic tests for.

    Returns
    -------
    list[TestCase]
        Typically two cases: one happy-path, one error-path.
    """
    cases: list[TestCase] = []

    # Happy path
    cases.append(
        TestCase(
            name=f"test_{func.name}_happy_path",
            function_under_test=func.qualified_name,
            description=f"Basic invocation of {func.qualified_name}",
            expected_behavior="Returns without error for typical input",
            strategy="basic",
        )
    )

    # Error path -- pass None when function has required non-optional params
    required = [
        p for p in func.parameters
        if p.name != "self" and not p.is_optional
    ]
    if required:
        cases.append(
            TestCase(
                name=f"test_{func.name}_none_input",
                function_under_test=func.qualified_name,
                description="Pass None for required parameters to test error handling",
                inputs={p.name: "None" for p in required},
                expected_behavior="Raises TypeError or handles None gracefully",
                strategy="error",
                is_edge_case=True,
            )
        )

    return cases
