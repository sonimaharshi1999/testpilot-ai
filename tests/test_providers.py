# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for LLM provider abstraction."""

from __future__ import annotations

import pytest

from testpilot.models import FunctionInfo, ParameterInfo, TestCase, TypeCategory
from testpilot.providers import NoneProvider, get_provider
from testpilot.providers.base import LLMProvider
from testpilot.providers.api_provider import APIProvider
from testpilot.providers.claude_cli import ClaudeCLIProvider


def _make_func() -> FunctionInfo:
    """Helper to create a simple FunctionInfo."""
    return FunctionInfo(
        name="example",
        module_path="test_mod",
        lineno=1,
        parameters=[
            ParameterInfo(
                name="n", annotation="int", type_category=TypeCategory.INTEGER
            )
        ],
        source_code="def example(n: int) -> int:\n    return n * 2\n",
    )


class TestNoneProvider:
    """Tests for the no-op provider."""

    def test_is_available(self) -> None:
        """NoneProvider is always available."""
        p = NoneProvider()
        assert p.is_available() is True

    def test_name(self) -> None:
        p = NoneProvider()
        assert p.name == "none"

    def test_enhance_passthrough(self) -> None:
        """enhance_test_cases returns cases unchanged."""
        p = NoneProvider()
        func = _make_func()
        cases = [TestCase(name="test_x", function_under_test="x")]
        result = p.enhance_test_cases(func, cases)
        assert result is cases

    def test_generate_assertion(self) -> None:
        """generate_assertion returns a TODO comment."""
        p = NoneProvider()
        func = _make_func()
        tc = TestCase(name="test_x", function_under_test="x")
        assertion = p.generate_assertion(func, tc)
        assert assertion.startswith("# TODO")


class TestAPIProvider:
    """Tests for the API provider stub."""

    def test_not_available_without_config(self) -> None:
        """APIProvider not available without key/url."""
        p = APIProvider()
        assert p.is_available() is False

    def test_available_with_config(self) -> None:
        """APIProvider available when key and url set."""
        p = APIProvider(api_key="test", base_url="http://localhost")
        assert p.is_available() is True

    def test_enhance_returns_cases(self) -> None:
        """Stub returns original cases."""
        p = APIProvider()
        func = _make_func()
        cases = [TestCase(name="test_x", function_under_test="x")]
        result = p.enhance_test_cases(func, cases)
        assert result == cases


class TestClaudeCLIProvider:
    """Tests for the Claude CLI provider."""

    def test_name(self) -> None:
        p = ClaudeCLIProvider()
        assert p.name == "claude_cli"

    def test_is_available_checks_path(self) -> None:
        """is_available returns a boolean based on PATH."""
        p = ClaudeCLIProvider()
        # This should not raise -- just returns True or False
        result = p.is_available()
        assert isinstance(result, bool)


class TestGetProvider:
    """Tests for the provider factory."""

    def test_get_none(self) -> None:
        p = get_provider("none")
        assert isinstance(p, NoneProvider)

    def test_get_claude_cli(self) -> None:
        p = get_provider("claude_cli")
        assert isinstance(p, ClaudeCLIProvider)

    def test_get_api(self) -> None:
        p = get_provider("api")
        assert isinstance(p, APIProvider)

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown_provider")
