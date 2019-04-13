import abc
import collections


class FieldHashCollection(abc.ABC):
    def __init__(self):
        self._contents = []
        self.dict = collections.defaultdict(lambda: collections.defaultdict(list))
        self.updated = False

    @property
    def contents(self):
        return self._contents[:]

    def append(self, entry: any):
        self._contents.append(entry)
        self._add_to_dict(entry)

    def _add_to_dict(self, entry: any):
        raise NotImplementedError

    def sort(self, reverse=False):
        self._contents = sorted(self.contents, reverse=reverse)


class JsonLoadedCollection(FieldHashCollection, abc.ABC):
    @staticmethod
    def json_entry_to_content(json_entry: dict):
        raise NotImplementedError
