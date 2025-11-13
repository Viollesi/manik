"""Basic package import tests."""

from manik_bot import __version__


def test_package_has_version() -> None:
    """Check that the package is importable."""
    assert __version__ == "0.1.0"

