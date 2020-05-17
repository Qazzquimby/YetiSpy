"""Data objects for working with groups of cards"""
import typing
from collections import defaultdict

import models.card


def make_card_playset_dict() -> typing.Dict:
    """Makes a dict representing card playsets
     CardId -> (list of 4 values corresponding to card counts)"""

    def _values_factory():
        return [0] * 4

    return defaultdict(_values_factory)


def make_collection_from_ew_export(
        cards: typing.List[typing.Dict[str, int]]
) -> typing.Dict[models.card.CardId, int]:
    """Gets card ownership from the Eternal Warcry export format."""
    collection = defaultdict(int)
    for card in cards:
        card_id = models.card.CardId(set_num=card["set"],
                                     card_num=card["card_number"])
        collection[card_id] += card["count"]
    return collection
