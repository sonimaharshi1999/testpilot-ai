# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Claude CLI LLM provider -- calls ``claude -p`` via subprocess.

This provider shells out to the ``claude`` CLI (Anthropic's Claude Code)
in print mode so no API key is required; the user just needs the CLI
installed and authenticated.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from typing import Any

from testpilot.models import FunctionInfo, TestCase
from testpilot.providers.base import LLMProvider


class ClaudeCLIProvider(LLMProvider):
    """LLM provider that delegates to the ``claude`` CLI."""

    def __init__(self, timeout: int = 60, **kwargs: Any) -> None:
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "claude_cli"

    def is_available(self) -> bool:
        """Check whether the ``claude`` binary is on PATH."""
        return shutil.which("claude") is not None

    def _call_claude(self, prompt: str) -> str:
        """Run ``claude -p '<prompt>'`` and return stdout.

        Parameters
        ----------
        prompt:
            The prompt string to send.

        Returns
        -------
        str
            The CLI's stdout output.

        Raises
        ------
        RuntimeError
            If the subprocess fails or times out.
        """
        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"claude CLI exited with code {result.returncode}: "
                    f"{result.stderr[:500]}"
                )
            return result.stdout.strip()
        except FileNotFoundError:
            raise RuntimeError(
                "claude CLI not found. Install it or use --provider none."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"claude CLI timed out after {self._timeout}s"
            )

    def enhance_test_cases(
        self,
        func: FunctionInfo,
        existing_cases: list[TestCase],
    ) -> list[TestCase]:
        """Ask Claude to suggest additional test cases.

        Parameters
        ----------
        func:
            The function under test.
        existing_cases:
            Already-generated test cases from strategies.

        Returns
        -------
        list[TestCase]
            Original cases plus any LLM-suggested additions.
        """
        existing_names = [c.name for c in existing_cases]
        prompt = textwrap.dedent(f"""\
            Analyze this Python function and suggest up to 3 additional
            pytest test case names and one-line descriptions that are NOT
            already in the existing list. Return ONLY a JSON array of
            objects with keys "name" and "description". No markdown.

            Function source:
            ```
            {func.source_code}
            ```

            Existing tests: {json.dumps(existing_names)}
        """)

        try:
            raw = self._call_claude(prompt)
            # Try to parse JSON from the response
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                suggestions = json.loads(raw[start:end])
            else:
                return existing_cases

            for s in suggestions:
                if isinstance(s, dict) and "name" in s:
                    existing_cases.append(
                        TestCase(
                            name=s["name"],
                            function_under_test=func.qualified_name,
                            description=s.get("description", ""),
                            strategy="llm",
                        )
                    )
        except (RuntimeError, json.JSONDecodeError, KeyError):
            pass  # LLM enhancement is best-effort

        return existing_cases

    def generate_assertion(
        self,
        func: FunctionInfo,
        test_case: TestCase,
    ) -> str:
        """Ask Claude to write a concrete assertion.

        Parameters
        ----------
        func:
            The function under test.
        test_case:
            The test case needing an assertion.

        Returns
        -------
        str
            A Python assertion line.
        """
        prompt = textwrap.dedent(f"""\
            Given this Python function, write ONE pytest assertion line.
            Return ONLY the assertion line, no explanation.

            Function:
            ```
            {func.source_code}
            ```

            Test scenario: {test_case.description}
            Inputs: {test_case.inputs}
        """)

        try:
            result = self._call_claude(prompt)
            line = result.strip().splitlines()[0]
            if line.startswith("assert") or line.startswith("#"):
                return line
        except (RuntimeError, IndexError):
            pass

        return f"# TODO: add assertion for {func.qualified_name}"
