from __future__ import annotations

from abc import ABCMeta

from eternal_collection_guide.deck_searches import DeckSearch

"""Base classes and utilities for learner objects."""
import datetime
import json
import os
import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from .field_hash_collection import FieldHashCollection


@dataclass
class JsonCompatible(metaclass=ABCMeta):
    """An object which can be loaded from JSON."""

    def to_json(self):
        return self

    @classmethod
    def from_json(cls, entry: dict):
        """Creates an instance of the object from a JSON object."""
        # noinspection PyArgumentList
        result = cls(**entry)
        return result


class PersistInterface(metaclass=ABCMeta):
    """Facilitates saving and loading objects."""

    def __init__(self, file_prefix: str,
                 file_name: str,
                 collection_type: typing.Type[FieldHashCollection]):
        self.file_prefix = file_prefix
        self.file_name = file_name
        self.collection_type = collection_type
        self.path = f"{self.file_prefix}/{self.file_name}"

    def load_empty(self) -> FieldHashCollection:
        """Loads an empty collection, ignoring any saved data.

        :return: an empty collection of the class's collection_type.
        """
        collection = self.collection_type()
        return collection

    def load(self) -> FieldHashCollection:
        """Loads the json collection from the saved file, if it exists.

        :return: The loaded collection.
        """
        raise NotImplementedError

    def save(self, collection: FieldHashCollection):
        """Saves the given collection.

        :param collection: The collection to save.
        """
        raise NotImplementedError


# class SQLInterface(PersistInterface):
#     """Facilitates saving and loading of objects to an SQL db."""
#
#     def load(self) -> FieldHashCollection:
#         pass
#
#     def save(self, collection: FieldHashCollection):
#         connection = self._get_connection()
#
#     def _get_connection(self):
#         db_filename = f"{self.file_prefix}/db.db"
#         connection = sqlite3.connect(db_filename)
#         connection.execute("""
#         CREATE TABLE IF NOT EXISTS ? (
#             first_name TEXT,
#             last_name  TEXT,
#             age        FLOAT
#         )
#         """)
#
#         blah = """
# INSERT INTO person (first_name, last_name, age)
# VALUES (?, ?, ?)
# """, ('chris', 'ostrouchov', 27)
#
#         return connection


class JsonInterface(PersistInterface):
    """Facilitates saving and loading of objects to JSON files."""

    def load(self) -> FieldHashCollection:
        json_entries = _JsonLoader(self.path).load_json_entries()
        collection = self._get_collection_from_json_entries(json_entries)
        return collection

    def save(self, collection: FieldHashCollection):
        print("Saving work. Do not close program.")

        def _encode(obj):
            if isinstance(obj, JsonCompatible):
                return obj.to_json().__dict__
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return obj.__dict__

        with open(self.path, "w") as file:
            json.dump(collection.contents, file, indent=4, sort_keys=True, default=_encode, )
        print("Saved.")

    def _get_collection_from_json_entries(self, json_entries: typing.List[any]) -> FieldHashCollection:
        collection = self.collection_type()
        for json_entry in json_entries:
            content = self._json_entry_to_content(json_entry)
            collection.append(content)
        return collection

    def _json_entry_to_content(self, json_entry):
        content = self.collection_type.content_type.from_json(json_entry)
        return content


class _JsonLoader:
    def __init__(self, path):
        self.path = path

    def load_json_entries(self) -> typing.List[dict]:
        """Loads the contents of the file at path.

        :return: The entries found in the json file.
        """
        self._create_file_if_not_exists()
        with open(self.path) as json_file:
            json_entries = self._read_json(json_file)
        return json_entries

    def _create_file_if_not_exists(self):
        try:
            open(self.path)
        except FileNotFoundError:
            self._create_file()

    def _create_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w+') as file:
            file.write("{}")

    @staticmethod
    def _read_json(json_file: typing.TextIO):
        try:
            json_entries = json.load(json_file)
        except json.decoder.JSONDecodeError:
            json_entries = []
        return json_entries


class BaseLearner(metaclass=ABCMeta):
    """A collection which populates itself by some method and saves its contents in JSON."""

    def __init__(self, file_prefix: str, file_name: str,
                 collection_type: typing.Type[FieldHashCollection],
                 max_days_before_update: int = 30,
                 dependent_paths=None):
        if dependent_paths is None:
            dependent_paths = []

        self._dependent_paths = dependent_paths

        self.json_interface = JsonInterface(file_prefix, file_name, collection_type)
        self._max_days_before_update = max_days_before_update

        self.collection = self._load()

        self._update_if_old()

    def update(self):
        """Repopulates the collection"""
        print(f"Updating {self.json_interface.file_name}")
        self._update_collection()
        self._save()
        self.collection.updated = True

    def _update_if_old(self):
        if self._is_old():
            self.update()

    def _is_old(self):
        if len(self.collection.contents) == 0:
            return True

        if self._days_since_last_update(self.json_interface.path) >= self._max_days_before_update:
            return True

        for dependent_path in self._dependent_paths:
            days_since_last_update = self._days_since_last_update(dependent_path)
            if days_since_last_update == 0:  # Dependency just updated. fixme this is a little gross. Could use flags.
                return True
        return False

    @staticmethod
    def _days_since_last_update(path):
        try:
            last_modified_time_stamp = os.path.getmtime(path)
        except FileNotFoundError:
            return 0
        last_modified_time = datetime.datetime.fromtimestamp(last_modified_time_stamp)
        time_since_last_modified = datetime.datetime.now() - last_modified_time
        days_since_last_modified = time_since_last_modified.days
        return days_since_last_modified

    def _update_collection(self):
        raise NotImplementedError

    def _load(self):
        collection = self.json_interface.load()
        return collection

    def _save(self):
        self.json_interface.save(self.collection)


# noinspection PyAbstractClass
class DeckSearchLearner(BaseLearner, metaclass=ABCMeta):
    """A BaseLearner that corresponds to an Eternal Warcry deck search."""

    def __init__(self, file_prefix: str,
                 file_name: str,
                 collection_type: typing.Type[FieldHashCollection],
                 deck_search: DeckSearch,
                 max_days_before_update: int = 30,
                 dependent_paths=None):
        search_urls_path = "../search_urls.csv"
        if dependent_paths is None:
            dependent_paths = [search_urls_path]
        else:
            dependent_paths += [search_urls_path]

        super().__init__(file_prefix, file_name, collection_type, max_days_before_update,
                         dependent_paths=dependent_paths)
        self.collection.deck_search = deck_search
