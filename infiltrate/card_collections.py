"""Data objects for working with cards"""
import typing
from collections import defaultdict
from typing import NamedTuple

from infiltrate import models, caches


class CardId(NamedTuple):
    """A key to identify a card."""
    set_num: int
    card_num: int


class CardPlayset(NamedTuple):
    """Mutliple copies of a card"""
    card_id: CardId
    count: int


class CardIdWithValue(NamedTuple):
    """The value of a given count of a card.

    The value is for the count-th copy of a card."""
    card_id: CardId
    count: int
    value: float


class CardDisplay:
    """Use make_card_display to use cached creation"""

    def __init__(self, card_id: CardId):
        card = models.card.get_card(card_id.set_num, card_id.card_num)
        self.set_num = card.set_num
        self.card_num = card.card_num
        self.name = card.name
        self.rarity = card.rarity
        self.image_url = card.image_url
        self.details_url = card.details_url


@caches.mem_cache.cache("card_displays", expire=3600)
def make_card_display(card_id: CardId):
    """Makes a CardValueDisplay, utilizing the cache to avoid repeated work."""
    card_display = CardDisplay(card_id)
    return card_display


class CardValueDisplay:
    """A bundle of raw and computed values corresponding to a card, to be used in the front end."""

    def __init__(self, card_id_with_value: CardIdWithValue):
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
