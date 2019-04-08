import abc
import datetime
import json
import typing

from field_hash_collection import FieldHashCollection


class BaseLearner(abc.ABC):
    def __init__(self, file_prefix: str, file_name: str,
                 collection_type: typing.Type[FieldHashCollection]):
        self.file_prefix = file_prefix
        self.file_name = file_name
        self.collection_type = collection_type

        self.updated = False
        self.path = f"{self.file_prefix}/{self.file_name}"
        self.contents = None
        self._load()

    def update(self):
        self._update_contents()
        self._save()
        self.contents.updated = True

    def _update_contents(self):
        raise NotImplementedError

    def _load(self):
        contents = self.collection_type()
        try:
            open(self.path)
        except FileNotFoundError:
            self._create_file()
        with open(self.path) as json_file:
            json_entries = json.load(json_file)
        for json_entry in json_entries:
            content = self._json_entry_to_content(json_entry)
            contents.append(content)
        self.contents = contents

    def _create_file(self):
        with open(self.path, 'w+') as file:
            file.write("{}")

    def _json_entry_to_content(self, json_entry):
        raise NotImplementedError

    def _save(self):
        print("Saving work. Do not close program.")

        def encode(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            else:
                return obj.__dict__

        with open(self.path, "w") as file:
            json.dump(self.contents.contents, file, indent=4, sort_keys=True, default=encode)
        print("Saved.")
