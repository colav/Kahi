import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import importlib


kahi_module = importlib.import_module("kahi.Kahi")
Kahi = kahi_module.Kahi


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = {
            document["_id"]: deepcopy(document) for document in documents or []
        }

    def find_one(self, query):
        return deepcopy(self.documents.get(query.get("_id")))


class FakeDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, FakeCollection())

    def list_collection_names(self):
        return list(self.collections)


class FakeClient:
    def __init__(self):
        self.databases = {"dam": FakeDatabase(), "target": FakeDatabase()}

    def __getitem__(self, name):
        return self.databases.setdefault(name, FakeDatabase())


class ReleaseReferenceTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.db = self.client["dam"]
        self.collections = {
            "works": "works_v1",
            "projects": "projects_v1",
            "patents": "patents_v1",
            "events": "events_v1",
            "persons": "persons_v1",
            "affiliations": "affiliations_v1",
        }
        self.runs = {entity: entity + "_run_v1" for entity in self.collections}
        for collection in self.collections.values():
            self.db.collections[collection] = FakeCollection([{"_id": "proof"}])
        self.db.collections["scienti_final_release_publications"] = FakeCollection([
            {
                "_id": "current", "current_release": "release_v1",
                "audit": "release_v1_audit", "collections": self.collections,
            },
            {
                "_id": "release_v1", "status": "published", "entity_count": 6,
                "audit": "release_v1_audit", "collections": self.collections,
                "materialization_runs": self.runs,
            },
        ])
        self.db.collections["scienti_final_release_audits"] = FakeCollection([{
            "_id": "release_v1_audit", "release_name": "release_v1",
            "status": "passed", "critical_anomalies": 0,
            "collections": self.collections, "materialization_runs": self.runs,
        }])

    def workflow_file(self):
        content = """
config:
  database_url: mongodb://target
  database_name: target
  log_database: target
  log_collection: log
  profile: false
  release_references:
    minciencias_open_data_current:
      database_url: mongodb://source
      database_name: dam
      publication_collection: scienti_final_release_publications
      audit_collection: scienti_final_release_audits
      expected_entities: [works, projects, patents, events, persons, affiliations]
workflow:
  minciencias_opendata_affiliations:
    release_ref: minciencias_open_data_current
  minciencias_opendata_person:
    release_ref: minciencias_open_data_current
"""
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
        handle.write(content)
        handle.close()
        self.addCleanup(Path(handle.name).unlink)
        return handle.name

    def test_resolves_once_and_injects_the_exact_release(self):
        with patch.object(kahi_module, "MongoClient", return_value=self.client):
            runner = Kahi(self.workflow_file())
            runner.load_workflow()

        for task in runner.workflow.values():
            self.assertEqual(task["release_name"], "release_v1")
            self.assertNotIn("release_ref", task)
        self.assertEqual(
            runner.resolved_release_references[
                "minciencias_open_data_current"
            ]["release_name"],
            "release_v1",
        )

    def test_rejects_a_release_with_a_failed_audit(self):
        self.db["scienti_final_release_audits"].documents[
            "release_v1_audit"
        ]["status"] = "failed"
        with patch.object(kahi_module, "MongoClient", return_value=self.client):
            with self.assertRaisesRegex(RuntimeError, "complete audited release"):
                Kahi(self.workflow_file()).load_workflow()

    def test_resume_requires_the_same_resolved_release(self):
        logs = [{
            "_id": "minciencias_opendata_works", "status": 0,
            "config": {"release_name": "release_v1", "task": None},
        }]
        self.assertTrue(Kahi._completed_log_matches(
            logs, "minciencias_opendata_works",
            {"release_name": "release_v1", "task": None},
        ))
        self.assertFalse(Kahi._completed_log_matches(
            logs, "minciencias_opendata_works",
            {"release_name": "release_v2", "task": None},
        ))


if __name__ == "__main__":
    unittest.main()
