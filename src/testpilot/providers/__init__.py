# MIT License
# Copyright (c) 2024 Maharshi Soni

"""LLM provider abstraction for TestPilot AI.

Providers are optional -- the core AST analysis and strategy-based test
generation works without any LLM. When an LLM provider is configured,
it enriches generated tests with more context-aware assertions.
"""

from testpilot.providers.base import LLMProvider, get_provider
from testpilot.providers.claude_cli import ClaudeCLIProvider
from testpilot.providers.api_provider import APIProvider
from testpilot.providers.none_provider import NoneProvider

__all__ = [
    "LLMProvider",
    "ClaudeCLIProvider",
    "APIProvider",
    "NoneProvider",
    "get_provider",
]
