# MIT License
# Copyright (c) 2024 Maharshi Soni

"""No-op LLM provider -- used when LLM enhancement is disabled.

This is the default provider. All methods pass through data unchanged,
so the core AST-based generation runs without any LLM dependency.
"""

from __future__ import annotations

from testpilot.models import FunctionInfo, TestCase
from testpilot.providers.base import LLMProvider


class NoneProvider(LLMProvider):
    """Pass-through provider that performs no LLM calls."""

    @property
    def name(self) -> str:
        return "none"

    def is_available(self) -> bool:
        return True

    def enhance_test_cases(
        self,
        func: FunctionInfo,
        existing_cases: list[TestCase],
    ) -> list[TestCase]:
        """Return cases unchanged -- no LLM enhancement."""
        return existing_cases

    def generate_assertion(
        self,
        func: FunctionInfo,
        test_case: TestCase,
    ) -> str:
        """Return a generic assertion placeholder."""
        return f"# TODO: add assertion for {func.qualified_name}"
