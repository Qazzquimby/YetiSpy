from __future__ import annotations

import typing
from abc import ABCMeta

from eternal_collection_guide.card import CardCollection, Card
from eternal_collection_guide.draft import DraftPack
from eternal_collection_guide.rarities import RARITIES
from eternal_collection_guide.sets import Sets, SetPack
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK
from eternal_collection_guide.values import ValueCollection


class CardPacks:
    """All available packs of cards in Eternal"""

    def __init__(self, sets: Sets, card_collection: CardCollection, value_collection: ValueCollection):
        self._sets = sets
        self._cards = card_collection
        self._values = value_collection

        self.set_to_card_pack = self._init_set_to_card_pack()
        self.draft_pack = DraftPack(self._cards, self._values)
        self.avg_newest_pack_value = self._init_avg_newest_pack_value()
        self.avg_golden_chest_pack_value = self._init_avg_golden_chest_pack_value()

    def _init_set_to_card_pack(self) -> typing.Dict[int, CardPack]:
        set_to_card_pack = {}

        for core_set in self._sets.core_sets:
            set_pack = SetPack(core_set.name, core_set.set_num, self._cards, self._values)
            set_to_card_pack[core_set.set_num] = set_pack

        return set_to_card_pack

    def _init_avg_newest_pack_value(self):
        newest_set = self._sets.newest_core_set
        newest_pack: CardPack = self.set_to_card_pack[newest_set.set_num]
        avg_value = newest_pack.avg_value

        return avg_value

    def _init_avg_golden_chest_pack_value(self):
        old_core_sets = self._sets.core_sets[:]
        old_core_sets.remove(self._sets.newest_core_set)

        old_card_packs: typing.List[CardPack] = [self.set_to_card_pack[core_set.set_num] for core_set in
                                                 old_core_sets]

        summed_value = sum(card_pack.avg_value for card_pack in old_card_packs)
        avg_value = summed_value / len(old_card_packs)
        return avg_value


class CardPack(metaclass=ABCMeta):
    """A pack of cards in Eternal"""

    def __init__(self, name: str, card_collection: CardCollection, value_collection: ValueCollection):
        self.name = name
        self.cards = card_collection
        self.value_sets = value_collection
        self.avg_value = self._init_avg_value()

    def get_cards_in_set(self) -> typing.List[Card]:
        """Get all cards in the set the pack belongs to."""
        raise NotImplementedError

    def _init_avg_value(self):
        values_in_rarity = self._get_values_in_rarity()
        avg_value_of_rarity = self._get_avg_value_of_rarity_dict(values_in_rarity)
        avg_value_of_pack = self._get_avg_value_of_pack(avg_value_of_rarity)
        return avg_value_of_pack

    def _get_value_of_card_by_name(self, card_name):
        value_sets = self.value_sets.dict["card_name"][card_name]
        if len(value_sets) == 0:
            return 0
        value_set = value_sets[0]
        return value_set.values[0]

    def _get_values_in_rarity(self) -> typing.Dict[str, typing.List[float]]:
        cards_in_set = self.get_cards_in_set()  # type: typing.List[Card]

        values_in_rarity = {}
        for rarity in RARITIES:
            values_in_rarity[rarity] = []

        for card in cards_in_set:
            value_of_card = self._get_value_of_card_by_name(card.name)
            rarity = card.rarity
            values_in_rarity[rarity].append(value_of_card)

        return values_in_rarity

    @staticmethod
    def _get_avg_value_of_rarity_dict(values_in_rarity: typing.Dict[str, typing.List[float]]) \
            -> typing.Dict[str, float]:
        avg_value_of_rarity = {}
        for rarity in RARITIES:
            total_value = 0
            for value in values_in_rarity[rarity]:
                total_value += value
            if total_value > 0:
                total_value /= len(values_in_rarity[rarity])
            avg_value_of_rarity[rarity] = total_value
        return avg_value_of_rarity

    @staticmethod
    def _get_avg_value_of_pack(avg_value_of_rarity_dict: typing.Dict[str, float]) -> float:
        avg_value_of_pack = 0
        for rarity in RARITIES:
            avg_value_of_rarity = avg_value_of_rarity_dict[rarity]
            num_in_pack = NUM_CARDS_IN_PACK[rarity]
            value_of_rarity_by_chance = avg_value_of_rarity * num_in_pack
            avg_value_of_pack += value_of_rarity_by_chance

        return avg_value_of_pack


