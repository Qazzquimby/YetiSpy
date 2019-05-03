import csv
import typing
from abc import ABCMeta

from eternal_collection_guide.card import CardCollection
from eternal_collection_guide.card_pack import Campaign, SetPack, CardPacks
from eternal_collection_guide.rarities import RARITIES
from eternal_collection_guide.sets import Sets, CardSet
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT
from eternal_collection_guide.values import ValueCollection


class BuyOption(metaclass=ABCMeta):

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


class BuyOptions(metaclass=ABCMeta):
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
        self.content = SetPack(set_name, set_num, cards, values)

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
        return self.content.avg_value


class BuyCampaigns(BuyOptions):
    def __init__(self, all_sets: Sets, cards: CardCollection, values: ValueCollection):
        sets = all_sets.campaigns
        super().__init__(cards, values, sets, BuyCampaign)


class BuyCampaign(BuyOption):
    def __init__(self, set_name, set_num, cards, values, card_packs):
        self.card_packs = card_packs
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


class BuyLeague(BuyOption):
    def __init__(self, card_packs: CardPacks):
        self.card_packs = card_packs

    @property
    def avg_gold_output(self) -> float:
        return 0

    @property
    def avg_shiftstone_output(self) -> float:
        return 0  # ignore for now

    @property
    def avg_value(self) -> float:
        with open("league.csv", "r") as league_file:
            csv_reader = csv.reader(league_file)
            rows = list(csv_reader)

        avg_value = 0
        for row in rows:
            set_num = int(row[0])
            avg_value_of_pack = self.card_packs.set_to_card_pack[set_num].avg_value
            num_packs = int(row[1])
            avg_value += avg_value_of_pack * num_packs

        return avg_value

    @property
    def gold_cost(self) -> int:
        return 12500
