# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Shared fixtures for TestPilot AI test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
CALCULATOR_FILE = SAMPLES_DIR / "calculator.py"
STRING_UTILS_FILE = SAMPLES_DIR / "string_utils.py"


@pytest.fixture
def calculator_path() -> Path:
    """Path to the sample calculator module."""
    return CALCULATOR_FILE


@pytest.fixture
def string_utils_path() -> Path:
    """Path to the sample string_utils module."""
    return STRING_UTILS_FILE


@pytest.fixture
def sample_source(tmp_path: Path) -> Path:
    """Create a minimal sample Python file for testing."""
    src = tmp_path / "sample.py"
    src.write_text(
        'def greet(name: str) -> str:\n'
        '    """Say hello."""\n'
        '    return f"Hello, {name}!"\n'
        "\n"
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n",
        encoding="utf-8",
    )
    return src


@pytest.fixture
def complex_source(tmp_path: Path) -> Path:
    """Create a more complex sample with classes and branches."""
    src = tmp_path / "complex.py"
    src.write_text(
        "class Processor:\n"
        '    """Process items."""\n'
        "\n"
        "    def __init__(self, threshold: int = 10) -> None:\n"
        "        self.threshold = threshold\n"
        "\n"
        "    def process(self, value: int) -> str:\n"
        "        if value < 0:\n"
        '            return "negative"\n'
        "        elif value < self.threshold:\n"
        '            return "low"\n'
        "        elif value == self.threshold:\n"
        '            return "exact"\n'
        "        else:\n"
        '            return "high"\n',
        encoding="utf-8",
    )
    return src
