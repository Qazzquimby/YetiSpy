from __future__ import annotations

"""Base classes and utilities for learner objects."""
import abc
import datetime
import json
import os
import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from eternal_collection_guide.field_hash_collection import JsonLoadedCollection


@dataclass(frozen=True)
class CollectionContent(abc.ABC):
    @classmethod
    def from_json_entry(cls, entry):
        # noinspection PyArgumentList
        card = cls(**entry)
        return card


class JsonInterface:
    """Facilitates saving and loading of objects to Json files."""

    def __init__(self, file_prefix: str,
                 file_name: str,
                 collection_type: typing.Type[JsonLoadedCollection]):
        self.file_prefix = file_prefix
        self.file_name = file_name
        self.collection_type = collection_type
        self.path = f"{self.file_prefix}/{self.file_name}"

        self._loader = _JsonLoader(self.path)

    def load_empty(self) -> JsonLoadedCollection:
        """Loads an empty collection, ignoring any saved data.

        :return: an empty collection of the class's collection_type.
        """
        collection = self.collection_type()
        return collection

    def load(self) -> JsonLoadedCollection:
        """Loads the json collection from the saved file, if it exists.

        :return: The loaded collection.
        """
        json_entries = self._loader.load_json_entries()
        collection = self._get_collection_from_json_entries(json_entries)
        return collection

    def save(self, collection: JsonLoadedCollection):
        """Saves the given collection.

        :param collection: The collection to save.
        """
        print("Saving work. Do not close program.")

        def _encode(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return obj.__dict__

        with open(self.path, "w") as file:
            json.dump(collection.contents, file, indent=4, sort_keys=True, default=_encode)
        print("Saved.")

    def _get_collection_from_json_entries(self, json_entries: typing.List[any]) -> JsonLoadedCollection:
        collection = self.collection_type()
        for json_entry in json_entries:
            content = self._json_entry_to_content(json_entry)
            collection.append(content)
        return collection

    def _json_entry_to_content(self, json_entry):
        content = self.collection_type.json_entry_to_content(json_entry)
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


class BaseLearner(abc.ABC):
    """A collection which populates itself by some method and saves its contents in Json."""

    def __init__(self, file_prefix: str, file_name: str,
                 collection_type: typing.Type[JsonLoadedCollection]):
        self.json_interface = JsonInterface(file_prefix, file_name, collection_type)

        self.collection = self._load()

    def update(self):
        """Repopulates the collection"""
        self._update_collection()
        self._save()
        self.collection.updated = True

    def _update_collection(self):
        raise NotImplementedError

    def _load(self):
        collection = self.json_interface.load()
        return collection

    def _save(self):
        self.json_interface.save(self.collection)
