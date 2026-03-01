"""Generate a scaffolded Kahi plugin package from a built-in template."""

from __future__ import annotations

import logging
from pathlib import Path
from shutil import copytree, move, rmtree

from kahi import templates

logger = logging.getLogger(__name__)


class PluginGenerator:
    """Create a ready-to-install Kahi plugin package from the bundled template.

    The generated plugin is a Python package that can be installed with *pip*
    and published on PyPI.
    """

    def __init__(self, name: str, prefix: str = "Kahi") -> None:
        """
        Parameters
        ----------
        name:
            Plugin name for the new project.
        prefix:
            Prefix for the generated project (default ``"Kahi"``).
        """
        self.name = name
        self._template_name = "template"
        self.prefix = prefix
        self._template_path = Path(templates.__file__).resolve().parent / "plugin" / "Kahi_template"

    # ------------------------------------------------------------------

    @staticmethod
    def _replace_in_file(path: Path, old: str, new: str) -> None:
        """Replace all occurrences of *old* with *new* inside *path*."""
        text = path.read_text()
        path.write_text(text.replace(old, new))

    def generate(self, path: str | Path | None = None) -> Path:
        """Generate the plugin scaffold.

        Parameters
        ----------
        path:
            Directory where the plugin project will be created.
            Defaults to the current working directory.

        Returns
        -------
        Path
            Path to the generated plugin directory.
        """
        base = Path(path) if path else Path.cwd()
        output_path = base / f"{self.prefix}_{self.name}"

        copytree(self._template_path, output_path)

        package_folder_old = output_path / "kahi_template"
        package_folder_new = output_path / f"{self.prefix}_{self.name}".lower()

        move(str(package_folder_old), str(package_folder_new))

        # Clean up any stale __pycache__ dirs
        for cache_dir in output_path.rglob("__pycache__"):
            rmtree(cache_dir, ignore_errors=True)

        package_file_old = package_folder_new / f"{self.prefix}_{self._template_name}.py"
        package_file_new = package_folder_new / f"{self.prefix}_{self.name}.py"
        package_file_old.rename(package_file_new)

        # Replace template placeholders
        for target in (
            package_file_new,
            output_path / "README.md",
            output_path / "setup.py",
            output_path / "MANIFEST.in",
        ):
            self._replace_in_file(target, self._template_name, self.name)

        logger.info("Plugin generated at %s", output_path)
        return output_path
