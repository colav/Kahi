"""Tests for the Kahi plugin scaffold generator."""

from pathlib import Path

from kahi.PluginGenerator import PluginGenerator


def test_plugin_generator_scaffolding(tmp_path: Path):
    """Test that a new plugin template is generated and modified correctly."""
    plugin_name = "testplugin"
    generator = PluginGenerator(plugin_name)

    # Generate the plugin inside our temporary directory
    output_dir = generator.generate(path=tmp_path)

    assert output_dir.exists()
    assert output_dir.name == "Kahi_testplugin"

    # Check that key files were created
    assert (output_dir / "setup.py").exists()
    assert (output_dir / "README.md").exists()

    # The actual python package folder should be lowercase
    pkg_folder = output_dir / "kahi_testplugin"
    assert pkg_folder.exists()

    plugin_file = pkg_folder / "Kahi_testplugin.py"
    assert plugin_file.exists()

    # Ensure placeholders were successfully overwritten
    plugin_content = plugin_file.read_text()
    assert "class Kahi_testplugin(KahiBase)" in plugin_content
    # shouldn't be template anymore
    assert "class Kahi_template(KahiBase)" not in plugin_content
