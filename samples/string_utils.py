# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Sample string utilities for TestPilot AI demos."""

from __future__ import annotations

from typing import Optional


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text) <= max_length:
        return text
    if max_length <= len(suffix):
        return suffix[:max_length]
    return text[: max_length - len(suffix)] + suffix


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split("_")
    if not parts:
        return ""
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def count_words(text: str) -> int:
    """Count the number of words in text."""
    return len(text.split())


def find_longest_word(text: str) -> Optional[str]:
    """Return the longest word in text, or None if empty."""
    words = text.split()
    if not words:
        return None
    return max(words, key=len)


def is_valid_email(email: str) -> bool:
    """Basic email validation (no regex, just structural check)."""
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    return True
