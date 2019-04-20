import typing

from eternal_collection_guide.card import CardCollection, COMMON, Card, UNCOMMON, RARE, LEGENDARY, RARITIES, PROMO
from eternal_collection_guide.values import ValueCollection

NUM_CARDS_IN_PACK = {COMMON: 8, UNCOMMON: 3, RARE: 0.9, LEGENDARY: 0.1, PROMO: 0.0}
RARITY_REGULAR_DISENCHANT = {COMMON: 1, UNCOMMON: 10, PROMO: 100, RARE: 200, LEGENDARY: 800}
RARITY_PREMIUM_DISENCHANT = {COMMON: 25, UNCOMMON: 50, PROMO: 400, RARE: 800, LEGENDARY: 3200}


class CardPack:
    def __init__(self, name: str, set_num: int, card_collection: CardCollection, value_collection: ValueCollection):
        self.name = name
        self.set_num = set_num
        self.cards = card_collection
        self.value_sets = value_collection

    @property
    def average_value(self):
        values_in_rarity = self._get_values_in_rarity()
        avg_value_of_rarity = self._get_avg_value_of_rarity_dict(values_in_rarity)
        avg_value_of_pack = self._get_avg_value_of_pack(avg_value_of_rarity)
        return avg_value_of_pack

    def get_cards_in_set(self):
        cards_in_set = self.cards.get_cards_in_set(self.set_num)
        return cards_in_set

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


class Campaign:
    def __init__(self, name: str, set_num: int, card_collection: CardCollection, value_collection: ValueCollection):
        self.name = name
        self.set_num = set_num
        self.cards = card_collection
        self.value_collection = value_collection

    @property
    def average_value(self):
        cards_in_set = self.get_cards_in_set()

        total_value = 0
        for card in cards_in_set:
            value_set_of_missing_cards = self._get_values_of_card_by_name(card.name)
            value = sum(value_set_of_missing_cards)
            total_value += value

        return total_value

    def get_cards_in_set(self):
        cards_in_set = self.cards.get_cards_in_set(self.set_num)
        return cards_in_set

    def _get_values_of_card_by_name(self, card_name):
        value_sets = self.value_collection.dict["card_name"][card_name]
        if len(value_sets) == 0:
            return [0]
        return value_sets[0].values
