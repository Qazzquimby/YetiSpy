"""Collections that populate with an automatically built dict to efficiently find values."""

import collections
import typing
from abc import ABCMeta

from eternal_collection_guide.base_learner import JsonCompatible
from eternal_collection_guide.deck_searches import DeckSearch

JsonCompatibleSub = typing.TypeVar('JsonCompatibleSub', bound=JsonCompatible)


class FieldHashCollection(typing.Generic[JsonCompatibleSub], metaclass=ABCMeta):
    """A collection of JsonCompatible with an automatically built dictionary for efficient searching."""
    content_type: typing.Type[JsonCompatibleSub]

    def __init__(self):
        self._contents = []
        self.dict = collections.defaultdict(lambda: collections.defaultdict(list))
        self.updated = False

    @property
    def contents(self) -> typing.List[JsonCompatibleSub]:
        return self._contents[:]

    def append(self, entry: any):
        self._contents.append(entry)
        self._add_to_dict(entry)

    def sort(self, key=None, reverse=False):
        self._contents = sorted(self.contents, key=key, reverse=reverse)

    def _add_to_dict(self, entry: any):
        raise NotImplementedError


class DeckSearchCollection(FieldHashCollection[JsonCompatibleSub], metaclass=ABCMeta):
    """A FieldHashCollection corresponding to an EternalWarcry deck search."""

    def __init__(self, deck_search: DeckSearch):
        self.deck_search = deck_search
        super().__init__()
