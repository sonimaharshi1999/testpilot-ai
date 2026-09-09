# MIT License
# Copyright (c) 2024 Maharshi Soni

"""Tests for the pytest plugin."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestPluginRegistration:
    """Test that the plugin registers correctly."""

    def test_plugin_imports(self) -> None:
        """The plugin module is importable."""
        from testpilot import plugin
        assert hasattr(plugin, "pytest_addoption")
        assert hasattr(plugin, "pytest_configure")
        assert hasattr(plugin, "pytest_sessionstart")

    def test_marker_registration(self, pytestconfig: pytest.Config) -> None:
        """The 'testpilot' marker is registered."""
        markers = pytestconfig.getini("markers")
        marker_names = [m.split(":")[0].strip() for m in markers]
        assert "testpilot" in marker_names
