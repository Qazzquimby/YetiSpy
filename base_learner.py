import abc
import datetime
import json

from field_hash_collection import FieldHashCollection


class BaseLearner(abc.ABC):
    def __init__(self, file_prefix: str, file_name: str):
        self.file_prefix = file_prefix
        self.file_name = file_name
        self.path = f"{self.file_prefix}/{self.file_name}"
        self.contents = self._load()

    def update(self):
        self._update_contents()
        self._save()

    def _update_contents(self):
        raise NotImplementedError

    def _load(self) -> FieldHashCollection:
        contents = FieldHashCollection()
        try:
            open(self.path)
        except FileNotFoundError:
            self._create_file()
        with open(self.path) as json_file:
            json_entries = json.load(json_file)
        for json_entry in json_entries:
            content = self._json_entry_to_content(json_entry)
            contents.append(content)
        return contents

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
            json.dump(self.contents._contents, file, indent=4, sort_keys=True, default=encode)
        print("Saved.")
