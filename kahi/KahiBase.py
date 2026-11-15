
class KahiBase:
    def __init__(self):
        pass

    def empty_affiliation(self):
        entry = {
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
            "campuses": []
        }
        return entry

    def empty_publisher(self):
        entry = {
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
            "products_count": 0
        }
        return entry

    def empty_source(self):
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
            "products_count": 0
        }

    def empty_subjects(self):
        return {
            "updated": [],
            "names": [],
            "abbreviations": [],
            "descriptions": [],
            "external_ids": [],
            "external_urls": [],
            "level": None,
            "relations": []
        }

    def empty_person(self):
        entry = {
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
            # Completed years at the release date; postcalculations fills it and clears birthdate.
            "age": None,
            "degrees": [],
            "subjects": [],
            "citations_count": [],
            "products_count": 0,
            "related_works": []
        }
        return entry

    def empty_work(self):
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
            "cited_by_api_url": "",
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

    def empty_event(self):
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
            "groups": []
        }

    def empty_project(self):
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
            "groups": []
        }

    def empty_patent(self):
        return {
            "titles": [],
            "updated": [],
            "abstracts": [],
            "types": [],
            "external_ids": [],
            "external_urls": [],
            "author_count": None,
            "authors": [],
            "ranking": [],
            "groups": [],
            "primary_topic": {},
            "topics": [],
        }

    def empty_work_other(self):
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
            "groups": []
        }

    def run(self):
        """
        entry point for the execution of the plugin, this method must be implemented
        """
        raise NotImplementedError(
            self.__class__.__name__ + '.run() not implemented')
