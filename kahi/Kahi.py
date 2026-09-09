import yaml
from importlib import import_module
import pkgutil
from collections import OrderedDict
from pymongo import MongoClient
from time import time
import cProfile
import pstats
import io
from pstats import SortKey
from copy import deepcopy


class OrderedLoader(yaml.SafeLoader):
    def __init__(self, *args, **kwargs):
        super(OrderedLoader, self).__init__(*args, **kwargs)

        def construct_dict_order(self, data):
            return OrderedDict(self.construct_pairs(data))
        self.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_dict_order)


class Kahi:
    def __init__(self, workflow_file, verbose=0, use_log=True):
        self.plugin_prefix = "kahi_"
        self.workflow_file = workflow_file
        self.workflow = None
        self.config = None
        self.plugins = {}
        self.resolved_release_references = {}

        self.client = None

        self.log_db = None
        self.log = None
        self.use_log = use_log
        self.verbose = verbose

    def load_workflow(self):
        """
        Loads the workflow from file
        """
        with open(self.workflow_file, "r") as stream:
            data = yaml.load(stream, Loader=OrderedLoader)
            self.workflow = data["workflow"]
            self.config = data["config"]
            self._resolve_release_references()
            self.client = MongoClient(self.config["database_url"])
            if self.verbose > 4:
                print(data)

    def _resolve_release_reference(self, name, definition):
        """Resolve and validate one immutable release from a published pointer."""
        database_url = definition.get(
            "database_url", self.config.get("database_url")
        )
        database_name = definition.get("database_name")
        if not database_url or not database_name:
            raise ValueError(
                "release reference {} requires database_url and database_name".format(
                    name
                )
            )
        publications_name = definition.get(
            "publication_collection", "scienti_final_release_publications"
        )
        audits_name = definition.get(
            "audit_collection", "scienti_final_release_audits"
        )
        pointer_id = definition.get("pointer_id", "current")
        pointer_field = definition.get("pointer_field", "current_release")

        source_client = MongoClient(database_url)
        source_db = source_client[database_name]
        pointer = source_db[publications_name].find_one({"_id": pointer_id}) or {}
        release_name = str(pointer.get(pointer_field) or "")
        if not release_name:
            raise RuntimeError(
                "release reference {} has no published target".format(name)
            )
        release = source_db[publications_name].find_one(
            {"_id": release_name}
        ) or {}
        audit_name = str(release.get("audit") or "")
        audit = source_db[audits_name].find_one({"_id": audit_name}) or {}
        collections = release.get("collections") or {}
        materialization_runs = release.get("materialization_runs") or {}
        expected_entities = set(definition.get("expected_entities") or [])
        available_collections = set(source_db.list_collection_names())
        missing_collections = sorted(
            collection for collection in collections.values()
            if collection not in available_collections
        )
        valid = (
            release.get("status") == "published"
            and audit.get("status") == "passed"
            and audit.get("release_name") == release_name
            and int(audit.get("critical_anomalies") or 0) == 0
            and audit.get("collections") == collections
            and pointer.get("audit") == audit_name
            and pointer.get("collections") == collections
            and not missing_collections
        )
        if expected_entities:
            valid = (
                valid
                and set(collections) == expected_entities
                and int(release.get("entity_count") or 0) == len(expected_entities)
                and set(materialization_runs) == expected_entities
                and audit.get("materialization_runs") == materialization_runs
            )
        if not valid:
            raise RuntimeError(
                "release reference {} does not point to a complete audited release".format(
                    name
                )
            )
        return {
            "release_name": release_name,
            "audit": audit_name,
            "collections": deepcopy(collections),
            "materialization_runs": deepcopy(materialization_runs),
        }

    def _resolve_release_references(self):
        """Pin every logical release reference once before any plugin runs."""
        definitions = self.config.get("release_references") or {}
        resolved = {}
        for log_id, params in self.workflow.items():
            if not isinstance(params, dict):
                continue
            reference = params.get("release_ref")
            if not reference:
                continue
            if "release_name" in params:
                raise ValueError(
                    "workflow task {} cannot define release_ref and release_name".format(
                        log_id
                    )
                )
            if reference not in definitions:
                raise ValueError(
                    "workflow task {} uses unknown release reference {}".format(
                        log_id, reference
                    )
                )
            if reference not in resolved:
                resolved[reference] = self._resolve_release_reference(
                    reference, definitions[reference]
                )
            params.pop("release_ref")
            params["release_name"] = resolved[reference]["release_name"]
        self.resolved_release_references = resolved

    @staticmethod
    def _completed_log_matches(logs, log_id, task_config):
        """Resume only when the successful task used the same configuration."""
        return any(
            log.get("_id") == log_id
            and log.get("status") == 0
            and log.get("config") == task_config
            for log in (logs or [])
        )

    def load_plugins(self, verbose=0):
        """
        Loads all plugins available in the system
        """
        discovered_plugins = {
            name: import_module(name)
            for finder, name, ispkg
            in pkgutil.iter_modules()
            if name.startswith(self.plugin_prefix + "_")
        }
        self.discovered_plugins = discovered_plugins

    def retrieve_logs(self):
        """
        Retrieves the logs from the database
        """

        self.log_db = self.client[self.config["log_database"]]
        log = list(self.log_db[self.config["log_collection"]].find())
        if log:
            self.log = log

        if self.verbose > 1:
            print("Log retrieved from database")
        if self.verbose > 4:
            print(log)

    def run(self):
        if not self.workflow:
            self.load_workflow()
        if not self.log:
            self.retrieve_logs()

        # import modules
        for module_name in self.workflow.keys():
            if self.verbose > 4:
                print("Loading plugin: " + self.plugin_prefix + module_name)
            if len(module_name.split("/")) > 1:
                module_name = module_name.split("/")[0]
            try:
                self.plugins[module_name] = import_module(
                    self.plugin_prefix + module_name + "." + self.plugin_prefix.capitalize() + module_name)
                self.plugins[module_name + "._version"] = import_module(
                    self.plugin_prefix + module_name + "._version")
            except ModuleNotFoundError as e:
                if self.verbose > 0 and self.verbose < 5:
                    print(e)
                    print("Plugin {} not found.\nTry\n\tpip install {}".format(
                        module_name,
                        self.plugin_prefix + module_name
                    ))
                    return None
                if self.verbose > 4:
                    raise

        # run workflow
        for log_id, params in self.workflow.items():
            executed_module = False
            log_split = log_id.split("/")
            if len(log_split) > 1:
                module_name = log_split[0]
                params["task"] = log_split[1]
            else:
                module_name = log_id

            plugin_config = self.config.copy()
            plugin_config[module_name] = self.workflow[log_id]
            if isinstance(plugin_config[module_name], list):
                for i in range(len(plugin_config[module_name])):
                    plugin_config[module_name][i]["task"] = params["task"] if "task" in params else None
            else:
                plugin_config[module_name]["task"] = params["task"] if "task" in params else None

            if self.use_log:
                executed_module = self._completed_log_matches(
                    self.log, log_id, plugin_config[module_name]
                )
            if executed_module:
                if self.verbose > 4:
                    print("Skipped plugin: " + self.plugin_prefix + log_id)
                continue
            if self.verbose > 4:
                print("Running plugin: " + self.plugin_prefix + log_id)

            plugin_class = getattr(
                self.plugins[module_name],
                self.plugin_prefix.capitalize() + module_name)

            plugin_class_version = getattr(
                self.plugins[module_name + "._version"], "get_version")

            plugin_instance = plugin_class(config=plugin_config)

            run = getattr(plugin_instance, "run")
            try:
                if self.config["profile"]:
                    pr = cProfile.Profile()
                    pr.enable()
                time_start = time()
                status = run()
                time_elapsed = time() - time_start
                if self.config["profile"]:
                    pr.disable()
                    s = io.StringIO()
                    sortby = SortKey.CUMULATIVE
                    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
                    ps.print_stats()
                    print(s.getvalue())
                if self.verbose > 4:
                    print("Plugin {} finished in {} seconds".format(
                        log_id,
                        time_elapsed
                    ))
                if self.use_log:
                    if self.log_db[self.config["log_collection"]
                                   ].find_one({"_id": log_id}):
                        self.log_db[self.config["log_collection"]].update_one(
                            {
                                "_id": log_id
                            },
                            {"$set":
                                {
                                    "plugin_version": plugin_class_version(),
                                    "config": plugin_config[module_name],
                                    "time": int(time_start),
                                    "status": status,
                                    "message": "ok",
                                    "time_elapsed": int(time_elapsed)
                                }
                             }
                        )
                    else:
                        self.log_db[self.config["log_collection"]].insert_one(
                            {
                                "_id": log_id,
                                "plugin_version": plugin_class_version(),
                                "config": plugin_config[module_name],
                                "time": int(time_start),
                                "status": status,
                                "message": "ok",
                                "time_elapsed": int(time_elapsed)
                            }
                        )
            except Exception as e:
                if self.use_log:
                    if self.log_db[self.config["log_collection"]
                                   ].find_one({"_id": log_id}):
                        self.log_db[self.config["log_collection"]].update_one(
                            {
                                "_id": log_id
                            },
                            {"$set":
                                {
                                    "plugin_version": plugin_class_version(),
                                    "config": plugin_config[module_name],
                                    "time": int(time()),
                                    "status": 1,
                                    "message": str(e),
                                    "time_elapsed": 0
                                }
                             }
                        )
                    else:
                        self.log_db[self.config["log_collection"]].insert_one(
                            {
                                "_id": log_id,
                                "plugin_version": plugin_class_version(),
                                "config": plugin_config[module_name],
                                "time": int(time()),
                                "status": 1,
                                "message": str(e),
                                "time_elapsed": 0
                            }
                        )
                print("Plugin {} failed".format(log_id))
                raise
        if self.verbose > 0:
            print("Workflow finished")
