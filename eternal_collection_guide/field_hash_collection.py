import abc
import collections
import typing

from eternal_collection_guide.base_learner import CollectionContent


class FieldHashCollection(abc.ABC):
    content_type: typing.Type[CollectionContent]

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

    def sort(self, key=None, reverse=False):
        self._contents = sorted(self.contents, key=key, reverse=reverse)


class JsonLoadedCollection(FieldHashCollection, abc.ABC):
    @classmethod
    def json_entry_to_content(cls, json_entry: dict) -> CollectionContent:
        return cls.content_type.from_json_entry(json_entry)
