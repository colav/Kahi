"""Tests for the main Kahi engine."""

import unittest.mock as mock
from pathlib import Path

import pytest
import yaml

from kahi.Kahi import Kahi


@pytest.fixture
def dummy_workflow(tmp_path: Path) -> Path:
    """Creates a temporary dummy workflow YAML file."""
    workflow_data = {
        "config": {
            "database_url": "mongodb://localhost:27017",
            "database_name": "kahi_test",
            "log_database": "kahi_log_test",
            "log_collection": "log",
        },
        "workflow": {"dummy_plugin/task1": {"some_param": 123}},
    }
    wf_path = tmp_path / "workflow_test.yaml"
    with open(wf_path, "w") as f:
        yaml.dump(workflow_data, f)

    return wf_path


def test_kahi_load_workflow(dummy_workflow: Path):
    """Test that workflow configuration loads properly into ordered structures."""
    with mock.patch("kahi.Kahi.MongoClient") as mock_mongo:
        kahi_engine = Kahi(str(dummy_workflow))
        kahi_engine.load_workflow()

        # Database URL config was loaded
        assert kahi_engine.config["database_name"] == "kahi_test"

        # MongoClient was initialized
        mock_mongo.assert_called_once_with("mongodb://localhost:27017")

        # Workflow is loaded
        assert "dummy_plugin/task1" in kahi_engine.workflow
        assert kahi_engine.workflow["dummy_plugin/task1"]["some_param"] == 123


def test_kahi_run_missing_plugin(dummy_workflow: Path, caplog):
    """Test what happens when a required plugin module doesn't exist."""
    with mock.patch("kahi.Kahi.MongoClient"):
        kahi_engine = Kahi(str(dummy_workflow), verbose=3)
        # Suppress log init to not need a real mongodb instance for this test
        kahi_engine.retrieve_logs = mock.MagicMock()
        # fake an empty log
        kahi_engine.log = []

        # This will attempt to import 'kahi_dummy_plugin.Kahidummy_plugin'
        # which will fail because the package doesn't exist.
        kahi_engine.run()

        # Ensure that it gracefully logs error instead of crashing if verbosity is right
        assert any("Plugin dummy_plugin not found" in rec.message for rec in caplog.records)
