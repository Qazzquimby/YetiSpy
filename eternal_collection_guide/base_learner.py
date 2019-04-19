import abc
import datetime
import json
import os
import typing

from eternal_collection_guide.field_hash_collection import JsonLoadedCollection


class JsonInterface:
    def __init__(self, file_prefix: str,
                 file_name: str,
                 collection_type: typing.Type[JsonLoadedCollection]):
        self.file_prefix = file_prefix
        self.file_name = file_name
        self.collection_type = collection_type
        self.path = f"{self.file_prefix}/{self.file_name}"

    def load_empty(self) -> JsonLoadedCollection:
        collection = self.collection_type()
        return collection

    def load(self) -> JsonLoadedCollection:
        json_entries = self._load_json_entries()
        collection = self.get_collection_from_json_entries(json_entries)
        return collection

    def _load_json_entries(self):
        self._create_file_if_not_exists()
        with open(self.path) as json_file:
            json_entries = self._read_json(json_file)
        return json_entries

    # noinspection PyMethodMayBeStatic
    def _read_json(self, json_file: typing.TextIO):
        try:
            json_entries = json.load(json_file)
        except json.decoder.JSONDecodeError:
            json_entries = []
        return json_entries

    def get_collection_from_json_entries(self, json_entries: typing.List[any]) -> JsonLoadedCollection:
        collection = self.collection_type()
        for json_entry in json_entries:
            content = self._json_entry_to_content(json_entry)
            collection.append(content)
        return collection

    def _json_entry_to_content(self, json_entry):
        content = self.collection_type.json_entry_to_content(json_entry)
        return content

    def save(self, collection: JsonLoadedCollection):
        print("Saving work. Do not close program.")

        def encode(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return obj.__dict__

        with open(self.path, "w") as file:
            json.dump(collection.contents, file, indent=4, sort_keys=True, default=encode)
        print("Saved.")

    def _create_file_if_not_exists(self):
        try:
            open(self.path)
        except FileNotFoundError:
            self._create_file()

    def _create_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w+') as file:
            file.write("{}")


class BaseLearner(abc.ABC):
    def __init__(self, file_prefix: str, file_name: str,
                 collection_type: typing.Type[JsonLoadedCollection]):
        self.json_interface = JsonInterface(file_prefix, file_name, collection_type)

        self.collection = self._load()

    def update(self):
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
