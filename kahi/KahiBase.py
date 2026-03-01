"""Base class that all Kahi plugins must extend."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KahiBase(ABC):
    """Abstract base class for Kahi plugins.

    Provides factory methods for common entity schemas used throughout the
    bibliographic data pipeline.  Subclasses **must** implement :meth:`run`.
    """

    # ------------------------------------------------------------------
    # Entity factories
    # ------------------------------------------------------------------

    @staticmethod
    def empty_affiliation() -> dict[str, Any]:
        return {
            "updated": [],
            "names": [],
            "aliases": [],
            "abbreviations": [],
            "types": [],
            "year_established": None,
            "status": [],
            "relations": [],
            "addresses": [],
            "external_urls": [],
            "external_ids": [],
            "subjects": [],
            "ranking": [],
            "description": [],
            "citation_count": [],
            "products_count": 0,
        }

    @staticmethod
    def empty_publisher() -> dict[str, Any]:
        return {
            "updated": [],
            "names": [],
            "aliases": [],
            "abbreviations": [],
            "lineage": [],
            "parent_publisher": None,
            "hierarchy_level": None,
            "types": [],
            "year_established": None,
            "status": [],
            "relations": [],
            "addresses": [],
            "external_urls": [],
            "external_ids": [],
            "subjects": [],
            "ranking": [],
            "description": [],
            "citation_count": [],
            "products_count": 0,
        }

    @staticmethod
    def empty_source() -> dict[str, Any]:
        return {
            "updated": [],
            "names": [],
            "abbreviations": [],
            "types": [],
            "keywords": [],
            "languages": [],
            "publisher": "",
            "relations": [],
            "addresses": [],
            "external_ids": [],
            "external_urls": [],
            "review_processes": [],
            "waiver": {},
            "plagiarism_detection": False,
            "open_access": [],
            "open_access_start_year": None,
            "publication_time_weeks": None,
            "apc": {},
            "copyright": {},
            "licenses": [],
            "subjects": [],
            "ranking": [],
            "citation_count": [],
            "products_count": 0,
        }

    @staticmethod
    def empty_subjects() -> dict[str, Any]:
        return {
            "updated": [],
            "names": [],
            "abbreviations": [],
            "descriptions": [],
            "external_ids": [],
            "external_urls": [],
            "level": None,
            "relations": [],
        }

    @staticmethod
    def empty_person() -> dict[str, Any]:
        return {
            "updated": [],
            "full_name": "",
            "first_names": [],
            "last_names": [],
            "initials": "",
            "aliases": [],
            "affiliations": [],
            "keywords": [],
            "external_ids": [],
            "sex": "",
            "marital_status": None,
            "ranking": [],
            "birthplace": {},
            "birthdate": -1,
            "degrees": [],
            "subjects": [],
            "citations_count": [],
            "products_count": 0,
            "related_works": [],
        }

    @staticmethod
    def empty_work() -> dict[str, Any]:
        return {
            "titles": [],
            "updated": [],
            "doi": "",
            "abstracts": [],
            "keywords": [],
            "types": [],
            "external_ids": [],
            "external_urls": [],
            "date_published": None,
            "year_published": None,
            "bibliographic_info": {},
            "open_access": {},
            "apc": {"paid": {}},
            "references_count": None,
            "references": [],
            "citations_count": [],
            "citations": [],
            "author_count": None,
            "authors": [],
            "source": {},
            "ranking": [],
            "subjects": [],
            "citations_by_year": [],
            "groups": [],
            "rights": [],
            "primary_topic": {},
            "topics": [],
        }

    @staticmethod
    def empty_event() -> dict[str, Any]:
        return {
            "titles": [],
            "updated": [],
            "abstract": "",
            "types": [],
            "external_ids": [],
            "external_urls": [],
            "date_held": None,
            "year_held": None,
            "author_count": None,
            "authors": [],
            "ranking": [],
            "groups": [],
        }

    @staticmethod
    def empty_project() -> dict[str, Any]:
        return {
            "titles": [],
            "updated": [],
            "abstract": "",
            "types": [],
            "external_ids": [],
            "external_urls": [],
            "date_init": None,
            "date_end": None,
            "year_init": None,
            "year_end": None,
            "author_count": None,
            "authors": [],
            "ranking": [],
            "groups": [],
        }

    @staticmethod
    def empty_patent() -> dict[str, Any]:
        return {
            "titles": [],
            "updated": [],
            "types": [],
            "external_ids": [],
            "external_urls": [],
            "author_count": None,
            "authors": [],
            "ranking": [],
            "groups": [],
        }

    @staticmethod
    def empty_work_other() -> dict[str, Any]:
        return {
            "titles": [],
            "updated": [],
            "abstract": "",
            "keywords": [],
            "types": [],
            "external_ids": [],
            "external_urls": [],
            "date_published": None,
            "year_published": None,
            "author_count": None,
            "authors": [],
            "ranking": [],
            "groups": [],
        }

    # ------------------------------------------------------------------
    # Plugin entry point
    # ------------------------------------------------------------------

    @abstractmethod
    def run(self) -> int:
        """Execute the plugin logic. Must be implemented by subclasses.

        Returns
        -------
        int
            Exit status code (0 = success).
        """
        ...
