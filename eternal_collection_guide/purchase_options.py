import abc
import typing

from eternal_collection_guide.card import RARITIES, CardCollection
from eternal_collection_guide.card_pack import CardPack, Campaign
from eternal_collection_guide.sets import Sets, CardSet
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT
from eternal_collection_guide.values import ValueCollection


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
    def avg_value_per_1000_gold(self):
        return self.avg_value * 1000 / self.effective_gold_cost

    def __lt__(self, other):
        return self.avg_value_per_1000_gold < other.avg_value_per_1000_gold

    def __eq__(self, other):
        return self.avg_value_per_1000_gold == other.avg_value_per_1000_gold


class BuyOptions(abc.ABC):
    def __init__(self, cards: CardCollection,
                 values: ValueCollection,
                 sets: typing.List[CardSet],
                 content_type: typing.Type):
        self.contents: typing.List[BuyOption] = self._init_contents(cards, values, sets, content_type)

    def _init_contents(self, cards: CardCollection,
                       values: ValueCollection,
                       sets: typing.List[CardSet],
                       content_type: typing.Type):
        contents = []
        for card_set in sets:
            content = content_type(card_set.name, card_set.set_num, cards, values)
            contents.append(content)
        return contents

    def __iter__(self):
        yield from self.contents


class BuyPacks(BuyOptions):
    def __init__(self, all_sets: Sets, cards: CardCollection, values: ValueCollection):
        sets = all_sets.core_sets
        super().__init__(cards, values, sets, BuyPack)


class BuyPack(BuyOption):
    def __init__(self, set_name, set_num, cards, values):
        super().__init__()
        self.content = CardPack(set_name, set_num, cards, values)

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
        return self.content.average_value


class BuyCampaigns(BuyOptions):
    def __init__(self, all_sets: Sets, cards: CardCollection, values: ValueCollection):
        sets = all_sets.campaigns
        super().__init__(cards, values, sets, BuyCampaign)


class BuyCampaign(BuyOption):
    def __init__(self, set_name, set_num, cards, values):
        super().__init__()
        self.content = Campaign(set_name, set_num, cards, values)

    @property
    def gold_cost(self) -> int:
        return 25000

    @property
    def avg_gold_output(self) -> float:
        return 0

    @property
    def avg_shiftstone_output(self) -> float:
        return 0

    @property
    def avg_value(self) -> float:
        return self.content.average_value

# class BuyDraft(BuyOption):
#     def __init__(self):
#         self.newest_set = NotImplemented  # fixme
#         self.newest_pack = NotImplementedError
#
#         self.draft_pack = NotImplementedError
#
#     @property
#     def gold_cost(self) -> int:
#         pass
#
#     @property
#     def avg_gold_output(self) -> float:
#         pass
#
#     @property
#     def avg_shiftstone_output(self) -> float:
#         400 + NotImplemented
#
#     @property
#     def avg_value(self) -> float:
#         pass
#         # take average value of cards in content
#         # Estimate n highest valued cards
#         # subtract their values from total
