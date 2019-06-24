import typing
from collections import defaultdict
from typing import NamedTuple


class CardId(NamedTuple):
    set_num: int
    card_num: int


class CardCountId(NamedTuple):
    card_id: CardId
    count: int


class CardIdWithValue(NamedTuple):
    card_id: CardId
    count: int
    value: float


def make_card_playset_dict() -> typing.Dict:
    def values_factory():
        return [0] * 4

    return defaultdict(values_factory)
