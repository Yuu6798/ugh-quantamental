"""Smoke tests for package bootstrap integrity."""

import ugh_quantamental


def test_package_imports() -> None:
    """Top-level package should be importable."""
    assert ugh_quantamental is not None


def test_version_exposed() -> None:
    """Package should expose a bootstrap version string."""
    assert ugh_quantamental.__version__ == "0.1.0"
