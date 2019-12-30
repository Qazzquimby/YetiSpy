"""Data objects for working with cards"""
import abc
import typing
from collections import defaultdict

import models.card


def make_card_playset_dict() -> typing.Dict:
    """Makes a default dict commonly used as CardId -> (list of 4 values corresponding to card counts)"""

    def _values_factory():
        return [0] * 4

    return defaultdict(_values_factory)


def make_collection_from_ew_export(cards: typing.List[typing.Dict[str, int]]) -> typing.Dict[models.card.CardId, int]:
    collection = defaultdict(int)
    for card in cards:
        card_id = models.card.CardId(set_num=card["set"], card_num=card["card_number"])
        collection[card_id] += card["count"]
    return collection


class PlaysetDict(abc.ABC):
    """Dict[CardID][Playset Size] = Some value"""

    def __init__(self):
        self._dict = make_card_playset_dict()

    def __getitem__(self, index):
        return self._dict[index]

    def keys(self):
        """As dict.keys()"""
        return self._dict.keys()


class ValueDict(PlaysetDict):
    """Dict[CardID][Playset Size] = Weighted value of that playset size"""

    def __iter__(self) -> models.card.CardIdWithValue:
        for card_id in self._dict.keys():
            for play_count in range(4):
                value = models.card.CardIdWithValue(card_id=card_id,
                                                    value=self._dict[card_id][play_count],
                                                    count=play_count + 1)
                yield value

    def add(self, other):
        """Adds another ValueDict to this one. Modifies in place."""
        for card_id in other.keys():
            for play_count in range(4):
                self[card_id][play_count] += other[card_id][play_count]


class PlayrateDict(PlaysetDict):
    """Dict[CardID][Playset Size] = Frequency of that playset size"""

    def _make_value_dict(self, weight: float, ) -> ValueDict:
        value_dict = ValueDict()

        for key in value_dict.keys():
            for playrate in range(4):
                value_dict[key][playrate] = self[key][playrate] * weight

        return value_dict
