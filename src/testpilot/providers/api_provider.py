# MIT License
# Copyright (c) 2024 Maharshi Soni

"""API-based LLM provider stub.

This provider is a placeholder for users who want to plug in their own
API key and call an HTTP endpoint directly. It does NOT ship with any
hard-coded API key -- the user must supply one via configuration.
"""

from __future__ import annotations

import json
import textwrap
from typing import Any

from testpilot.models import FunctionInfo, TestCase
from testpilot.providers.base import LLMProvider


class APIProvider(LLMProvider):
    """LLM provider that calls an HTTP API (user-supplied key).

    This is intentionally a stub that demonstrates the interface.
    Users would subclass or configure it with their own endpoint.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        **kwargs: Any,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    @property
    def name(self) -> str:
        return "api"

    def is_available(self) -> bool:
        """Check whether API key and base URL are configured."""
        return bool(self._api_key and self._base_url)

    def enhance_test_cases(
        self,
        func: FunctionInfo,
        existing_cases: list[TestCase],
    ) -> list[TestCase]:
        """Placeholder -- returns existing cases unchanged.

        In a production deployment the user would implement the HTTP
        call here using ``httpx`` or ``requests``.

        Parameters
        ----------
        func:
            The function under test.
        existing_cases:
            Already-generated test cases from strategies.

        Returns
        -------
        list[TestCase]
            Cases unchanged (stub).
        """
        if not self.is_available():
            return existing_cases
        # Stub: real implementation would POST to self._base_url
        return existing_cases

    def generate_assertion(
        self,
        func: FunctionInfo,
        test_case: TestCase,
    ) -> str:
        """Placeholder assertion generator.

        Parameters
        ----------
        func:
            The function under test.
        test_case:
            The test case needing an assertion.

        Returns
        -------
        str
            A placeholder assertion.
        """
        return f"# TODO: implement API-based assertion for {func.qualified_name}"
