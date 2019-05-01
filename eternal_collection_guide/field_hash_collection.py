"""Collections that populate with an automatically built dict to efficiently find values."""

import abc
import collections
import typing

from eternal_collection_guide.base_learner import CollectionContent


class FieldHashCollection(abc.ABC):
    """A collection CollectionContent with an automatically built dictionary for efficient searching."""
    content_type: typing.Type[CollectionContent]

    def __init__(self):
        self._contents = []
        self.dict = collections.defaultdict(lambda: collections.defaultdict(list))
        self.updated = False

    @property
    def contents(self) -> typing.List[CollectionContent]:
        return self._contents[:]

    def append(self, entry: any):
        self._contents.append(entry)
        self._add_to_dict(entry)

    def sort(self, key=None, reverse=False):
        self._contents = sorted(self.contents, key=key, reverse=reverse)

    def _add_to_dict(self, entry: any):
        raise NotImplementedError
