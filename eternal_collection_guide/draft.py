# Average value of drafted cards equal to average value of a pack (if we incorrectly assume other players have the same
# priorities as you)

# Average reward is 2 silver chests + 1 gold chest.
from eternal_collection_guide.card import RARITIES
from eternal_collection_guide.card_pack import DraftPack, SetPack
from eternal_collection_guide.purchase_options import BuyOption
from eternal_collection_guide.sets import Sets
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT


class BuyDraft(BuyOption):
    def __init__(self, cards, values):
        super().__init__()

        self.sets = Sets()
        newest_set = self.sets.newest_core_set

        self.contents = [
            SetPack(newest_set.name, newest_set.set_num, cards, values),
            SetPack(newest_set.name, newest_set.set_num, cards, values),
            SetPack(newest_set.name, newest_set.set_num, cards, values),
            DraftPack(cards, values),
            DraftPack(cards, values),
        ]

    @property
    def gold_cost(self) -> int:
        return 5000

    @property
    def avg_gold_output(self) -> float:
        return 1000

    @property
    def avg_shiftstone_output(self) -> float:
        total_shiftstone = 500  # flat value
        for rarity in RARITIES:
            num_cards = NUM_CARDS_IN_PACK[rarity]
            shiftstone_per_card = RARITY_REGULAR_DISENCHANT[rarity]
            shiftstone_for_rarity = num_cards * shiftstone_per_card
            total_shiftstone += 5 * shiftstone_for_rarity
        return total_shiftstone

    @property
    def avg_value(self) -> float:
        avg_value = 0
        for content in self.contents:
            avg_value += content.avg_value
        return avg_value
