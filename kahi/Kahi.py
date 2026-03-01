"""Kahi – core workflow engine for plugin-based ETL pipelines."""

from __future__ import annotations

import cProfile
import io
import logging
import pkgutil
import pstats
from collections import OrderedDict
from importlib import import_module
from pathlib import Path
from pstats import SortKey
from time import time
from typing import Any

import yaml
from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)


class _OrderedLoader(yaml.SafeLoader):
    """YAML loader that preserves insertion order."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        def _construct_ordered(loader: yaml.Loader, node: yaml.Node) -> OrderedDict[str, Any]:
            return OrderedDict(loader.construct_pairs(node))

        self.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_ordered)


class Kahi:
    """Main workflow engine that discovers and runs Kahi plugins."""

    PLUGIN_PREFIX = "kahi_"

    def __init__(self, workflow_file: str | Path, *, verbose: int = 0, use_log: bool = True) -> None:
        self.workflow_file = Path(workflow_file)
        self.workflow: OrderedDict[str, Any] | None = None
        self.config: dict[str, Any] | None = None
        self.plugins: dict[str, Any] = {}

        self.client: MongoClient | None = None  # type: ignore[type-arg]
        self.log_db: Database | None = None  # type: ignore[type-arg]
        self.log: list[dict[str, Any]] | None = None
        self.use_log = use_log
        self.verbose = verbose

        # Configure logging level based on verbosity
        if verbose >= 5:
            logging.basicConfig(level=logging.DEBUG)
        elif verbose >= 3:
            logging.basicConfig(level=logging.INFO)
        elif verbose >= 1:
            logging.basicConfig(level=logging.WARNING)

    # ------------------------------------------------------------------
    # Workflow loading
    # ------------------------------------------------------------------

    def load_workflow(self) -> None:
        """Load the workflow definition from a YAML file."""
        with self.workflow_file.open() as stream:
            data: dict[str, Any] = yaml.load(stream, Loader=_OrderedLoader)
            self.workflow = data["workflow"]
            self.config = data["config"]
            self.client = MongoClient(self.config["database_url"])
            logger.debug("Loaded workflow: %s", data)

    # ------------------------------------------------------------------
    # Plugin discovery
    # ------------------------------------------------------------------

    def load_plugins(self) -> dict[str, Any]:
        """Discover all installed kahi plugins and return them."""
        discovered_plugins = {
            name: import_module(name)
            for _finder, name, _ispkg in pkgutil.iter_modules()
            if name.startswith(f"{self.PLUGIN_PREFIX}_")
        }
        self.discovered_plugins = discovered_plugins
        return discovered_plugins

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def retrieve_logs(self) -> None:
        """Retrieve execution logs from the database."""
        assert self.client is not None and self.config is not None
        self.log_db = self.client[self.config["log_database"]]
        log = list(self.log_db[self.config["log_collection"]].find())
        if log:
            self.log = log

        logger.info("Log retrieved from database")
        logger.debug("Log contents: %s", log)

    def _upsert_log(self, log_id: str, doc: dict[str, Any]) -> None:
        """Insert or update a log entry in the database."""
        assert self.log_db is not None and self.config is not None
        collection = self.log_db[self.config["log_collection"]]
        if collection.find_one({"_id": log_id}):
            collection.update_one({"_id": log_id}, {"$set": doc})
        else:
            collection.insert_one({"_id": log_id, **doc})

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _import_plugin(self, module_name: str) -> bool:
        """Import a single plugin module and its version. Returns *True* on success."""
        try:
            self.plugins[module_name] = import_module(
                f"{self.PLUGIN_PREFIX}{module_name}.{self.PLUGIN_PREFIX.capitalize()}{module_name}"
            )
            self.plugins[f"{module_name}._version"] = import_module(f"{self.PLUGIN_PREFIX}{module_name}._version")
        except ModuleNotFoundError as exc:
            if self.verbose < 5:
                logger.error("%s", exc)
                logger.error(
                    "Plugin %s not found.\nTry\n\tpip install %s",
                    module_name,
                    f"{self.PLUGIN_PREFIX}{module_name}",
                )
                return False
            raise
        return True

    def _should_skip(self, log_id: str) -> bool:
        """Check whether *log_id* was already executed successfully."""
        if not self.use_log or not self.log:
            return False
        return any(entry["_id"] == log_id and entry["status"] == 0 for entry in self.log)

    def run(self) -> None:
        """Execute the full workflow."""
        if not self.workflow:
            self.load_workflow()
        if not self.log:
            self.retrieve_logs()

        assert self.workflow is not None and self.config is not None

        # --- Import all required plugin modules ---
        for raw_name in self.workflow:
            module_name = raw_name.split("/")[0]
            logger.debug("Loading plugin: %s%s", self.PLUGIN_PREFIX, module_name)
            if not self._import_plugin(module_name):
                return

        # --- Run each workflow step ---
        for log_id, params in self.workflow.items():
            log_split = log_id.split("/")
            module_name = log_split[0]
            if len(log_split) > 1:
                params["task"] = log_split[1]

            if self._should_skip(log_id):
                logger.debug("Skipped plugin: %s%s", self.PLUGIN_PREFIX, log_id)
                continue

            logger.debug("Running plugin: %s%s", self.PLUGIN_PREFIX, log_id)

            plugin_class = getattr(
                self.plugins[module_name],
                f"{self.PLUGIN_PREFIX.capitalize()}{module_name}",
            )
            plugin_class_version = getattr(self.plugins[f"{module_name}._version"], "get_version")

            # Build per-plugin config
            plugin_config: dict[str, Any] = self.config.copy()
            plugin_config[module_name] = self.workflow[log_id]
            task_value = params.get("task")
            if isinstance(plugin_config[module_name], list):
                for item in plugin_config[module_name]:
                    item["task"] = task_value
            else:
                plugin_config[module_name]["task"] = task_value

            plugin_instance = plugin_class(config=plugin_config)

            try:
                profiling = self.config.get("profile", False)
                pr: cProfile.Profile | None = None
                if profiling:
                    pr = cProfile.Profile()
                    pr.enable()

                time_start = time()
                status = plugin_instance.run()
                time_elapsed = time() - time_start

                if pr is not None:
                    pr.disable()
                    stream = io.StringIO()
                    pstats.Stats(pr, stream=stream).sort_stats(SortKey.CUMULATIVE).print_stats()
                    logger.info(stream.getvalue())

                logger.debug("Plugin %s finished in %.2f seconds", log_id, time_elapsed)

                if self.use_log:
                    self._upsert_log(
                        log_id,
                        {
                            "plugin_version": plugin_class_version(),
                            "config": plugin_config[module_name],
                            "time": int(time_start),
                            "status": status,
                            "message": "ok",
                            "time_elapsed": int(time_elapsed),
                        },
                    )

            except Exception as exc:
                if self.use_log:
                    self._upsert_log(
                        log_id,
                        {
                            "plugin_version": plugin_class_version(),
                            "config": plugin_config[module_name],
                            "time": int(time()),
                            "status": 1,
                            "message": str(exc),
                            "time_elapsed": 0,
                        },
                    )
                logger.error("Plugin %s failed", log_id)
                raise

        logger.info("Workflow finished")
