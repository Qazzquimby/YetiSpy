import abc
import typing

from eternal_collection_guide.card import RARITIES
from eternal_collection_guide.card_pack import CardPack, NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT
from eternal_collection_guide.sets import Sets


class BuyOption(abc.ABC):

    @property
    def gold_cost(self) -> int:
        raise NotImplementedError

    @property
    def avg_gold_output(self) -> float:
        raise NotImplementedError

    @property
    def avg_shiftstone_output(self) -> float:
        raise NotImplementedError

    @property
    def avg_value(self) -> float:
        raise NotImplementedError

    @property
    def effective_gold_cost(self):
        return self.gold_cost - self.avg_gold_output

    @property
    def value_per_1000_gold(self):
        return self.avg_value * 1000 / self.effective_gold_cost


class BuyPacks:
    def __init__(self, sets: Sets, cards, values):
        self.sets = sets
        self.packs: typing.List[BuyPack] = self._init_packs(cards, values)

    def __iter__(self):
        yield from self.packs

    def _init_packs(self, cards, values):
        packs = []
        for card_set in self.sets.core_sets:
            pack = BuyPack(card_set.set_num, cards, values)
            packs.append(pack)
        return packs


class BuyPack(BuyOption):
    def __init__(self, set_num, cards, values):
        super().__init__()
        self.card_pack = CardPack(set_num, cards, values)

    @property
    def gold_cost(self) -> int:
        return 1000

    @property
    def avg_gold_output(self) -> float:
        return 0

    @property
    def avg_shiftstone_output(self) -> float:
        total_shiftstone = 100  # flat value
        for rarity in RARITIES:
            num_cards = NUM_CARDS_IN_PACK[rarity]
            shiftstone_per_card = RARITY_REGULAR_DISENCHANT[rarity]
            shiftstone_for_rarity = num_cards * shiftstone_per_card
            total_shiftstone += shiftstone_for_rarity
        return total_shiftstone
        # todo much later convert shiftstone to value using enchant rates.

    @property
    def avg_value(self) -> float:
        return self.card_pack.average_value
