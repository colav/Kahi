"""Version information for Kahi (kept for backward compatibility)."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("Kahi")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0-dev"


def get_version() -> str:
    """Return the installed package version."""
    return __version__
