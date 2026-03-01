"""Kahi – ETL framework for bibliographic data with a plugin-based workflow."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("Kahi")
except PackageNotFoundError:  # pragma: no cover – editable / dev install
    __version__ = "0.0.0-dev"

from kahi.Kahi import Kahi
from kahi.KahiBase import KahiBase
from kahi.PluginGenerator import PluginGenerator

__all__ = [
    "__version__",
    "Kahi",
    "KahiBase",
    "PluginGenerator",
]
