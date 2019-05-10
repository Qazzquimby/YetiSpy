from __future__ import annotations

import csv
import typing
from abc import ABCMeta

import eternal_collection_guide.campaign
import eternal_collection_guide.card_pack as card_pack_mod
import eternal_collection_guide.sets
from eternal_collection_guide.rarities import RARITIES
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT

# todo get rid of leading folder name in imports.

if typing.TYPE_CHECKING:
    from eternal_collection_guide.card import CardCollection
    from eternal_collection_guide.sets import Sets, CardSet
    from eternal_collection_guide.values import ValueCollection


class BuyOption(metaclass=ABCMeta):
    """Something that can be bought in Eternal."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def gold_cost(self) -> int:
        raise NotImplementedError

    @property
    def gem_cost(self) -> int:
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

    @property
    def avg_value_per_100_gems(self):
        return self.avg_value * 100 / self.gem_cost

    @property
    def evaluation_string(self):
        return f"Buy {self.name}" + self._purchase_efficiency_string()

    def _purchase_efficiency_string(self):
        return f"  -  Value per 1000 gold = {self.avg_value_per_1000_gold}" \
            f"  -  Value per 100 gems = {self.avg_value_per_100_gems}\n"

    def __lt__(self, other):
        return self.avg_value_per_1000_gold < other.avg_value_per_1000_gold

    def __eq__(self, other):
        return self.avg_value_per_1000_gold == other.avg_value_per_1000_gold


class BuyNamedContentOption(BuyOption, metaclass=ABCMeta):
    """A named item that belongs to a category of things that can be bought in Eternal.

    Examples include a specific card pack, or a specific campaign.
    """

    def __init__(self, content):
        self.content = content

    @property
    def evaluation_string(self):
        return f"Buy {self.name}: {self.content.name}" + self._purchase_efficiency_string()


class BuyOptions(metaclass=ABCMeta):
    def __init__(self, cards: CardCollection,
                 values: ValueCollection,
                 sets: typing.List[CardSet],
                 content_type: typing.Type):
        self.contents: typing.List[BuyOption] = self._init_contents(cards, values, sets, content_type)

    @staticmethod
    def _init_contents(cards: CardCollection,
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


class BuyPack(BuyNamedContentOption):

    def __init__(self, set_name, set_num, cards, values):
        super().__init__(eternal_collection_guide.sets.SetPack(set_name, set_num, cards, values))

    @property
    def name(self) -> str:
        return "Pack"

    @property
    def gold_cost(self) -> int:
        return 1000

    @property
    def gem_cost(self) -> int:
        return 100

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


class BuyCampaign(BuyNamedContentOption):
    def __init__(self, set_name, set_num, cards, values):
        # self.card_packs = card_packs
        super().__init__(eternal_collection_guide.campaign.Campaign(set_name, set_num, cards, values))

    @property
    def name(self) -> str:
        return "Campaign"

    @property
    def gold_cost(self) -> int:
        return 25000

    @property
    def gem_cost(self) -> int:
        return 1000

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
    def __init__(self, card_packs: card_pack_mod.CardPacks):
        self.card_packs = card_packs

    @property
    def name(self):
        return "League"

    @property
    def avg_gold_output(self) -> float:
        return 0

    @property
    def avg_shiftstone_output(self) -> float:
        return 0  # ignore for now

    @property
    def avg_value(self) -> float:
        with open("../league.csv", "r") as league_file:
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

    @property
    def gem_cost(self) -> int:
        return 1100
