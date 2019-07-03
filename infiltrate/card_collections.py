"""Data objects for working with cards"""
import abc
import typing
from collections import defaultdict

from infiltrate import caches
from infiltrate import models
from infiltrate.models.card import CardDisplay, CardId


@caches.mem_cache.cache("card_displays", expire=3600)
def make_card_display(card_id: CardId):
    """Makes a CardValueDisplay, utilizing the cache to avoid repeated work."""
    card_display = CardDisplay(card_id)
    return card_display


class CardValueDisplay:
    """A bundle of raw and computed values corresponding to a card, to be used in the front end."""

    def __init__(self, card_id_with_value: models.card.CardIdWithValue):
        self.card: CardDisplay = make_card_display(card_id_with_value.card_id)

        self.count = card_id_with_value.count
        self.value = card_id_with_value.value

        cost = models.rarity.rarity_from_name[self.card.rarity].enchant
        self.value_per_shiftstone = card_id_with_value.value * 100 / cost


def make_card_playset_dict() -> typing.Dict:
    """Makes a default dict commonly used as CardId -> (list of 4 values corresponding to card counts)"""

    def _values_factory():
        return [0] * 4

    return defaultdict(_values_factory)


class PlaysetDict(abc.ABC):
    """Dict[CardID][Playset Size] = Some value"""

    def __init__(self):
        self._dict = make_card_playset_dict()

    def __getitem__(self, index):
        return self._dict[index]

    def __setitem__(self, index, value):
        self._dict[index] = value

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


class PlayrateDict(PlaysetDict):
    """Dict[CardID][Playset Size] = Frequency of that playset size"""

    def _make_value_dict(self, weight: float, ) -> ValueDict:
        value_dict = ValueDict()

        for key in value_dict.keys():
            for playrate in range(4):
                value_dict[key][playrate] = self[key][playrate] * weight

        return value_dict
