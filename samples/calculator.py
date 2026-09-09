# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Sample calculator module for TestPilot AI demos."""

from __future__ import annotations


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def divide(numerator: float, denominator: float) -> float:
    """Divide numerator by denominator.

    Raises
    ------
    ZeroDivisionError
        If denominator is zero.
    """
    if denominator == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return numerator / denominator


def clamp(value: int, low: int, high: int) -> int:
    """Clamp a value to the range [low, high]."""
    if value < low:
        return low
    if value > high:
        return high
    return value


def factorial(n: int) -> int:
    """Compute n! iteratively."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def is_palindrome(text: str) -> bool:
    """Check if text is a palindrome (case-insensitive)."""
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]


class Statistics:
    """Basic statistics calculator."""

    def __init__(self, data: list[float]) -> None:
        if not data:
            raise ValueError("Data must not be empty")
        self._data = list(data)

    def mean(self) -> float:
        """Calculate arithmetic mean."""
        return sum(self._data) / len(self._data)

    def median(self) -> float:
        """Calculate median value."""
        sorted_data = sorted(self._data)
        n = len(sorted_data)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_data[mid - 1] + sorted_data[mid]) / 2
        return sorted_data[mid]

    def variance(self) -> float:
        """Calculate population variance."""
        m = self.mean()
        return sum((x - m) ** 2 for x in self._data) / len(self._data)
