"""Tests for KahiBase abstract class and entity factory methods."""

import pytest

from kahi.KahiBase import KahiBase


class DummyPlugin(KahiBase):
    """Dummy plugin implementation to test KahiBase instantiation."""

    def run(self) -> int:
        return 0


def test_kahi_base_abstract():
    """Test that KahiBase cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        KahiBase()


def test_dummy_plugin_instantiation():
    """Test that subclass implementing run() can be instantiated."""
    plugin = DummyPlugin()
    assert plugin.run() == 0


@pytest.mark.parametrize(
    "factory_method, expected_keys",
    [
        (
            "empty_affiliation",
            ["updated", "names", "types", "external_ids", "ranking", "products_count"],
        ),
        (
            "empty_work",
            ["titles", "updated", "doi", "authors", "citations_count", "source"],
        ),
        (
            "empty_person",
            ["updated", "full_name", "first_names", "degrees", "products_count"],
        ),
        (
            "empty_source",
            ["updated", "names", "open_access", "publisher", "products_count"],
        ),
    ],
)
def test_kahi_base_entity_factories(factory_method, expected_keys):
    """Test that factory methods return dicts containing standard expected keys."""
    # We call it directly on KahiBase (since they are now @staticmethod)
    method = getattr(KahiBase, factory_method)
    entity = method()

    assert isinstance(entity, dict)
    for key in expected_keys:
        assert key in entity
