# Average value of drafted _cards equal to average value of a pack (if we incorrectly assume other players have the same
# priorities as you)

# Average reward is 2 silver chests + 1 gold chest.
from eternal_collection_guide.card import RARITIES
from eternal_collection_guide.card_pack import CardPacks
from eternal_collection_guide.purchase_options import BuyOption
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT


class BuyDraft(BuyOption):
    def __init__(self):
        super().__init__()

        self.num_newest_packs = 2
        self.num_draft_packs = 2

        self.avg_wins = 2.4
        self.avg_gold_chests = self.avg_wins - 1  # only works if avg_wins between 2 and 4
        self.estimated_draft_efficiency = 1.25

    @property
    def gold_cost(self) -> int:
        return 5000

    @property
    def avg_gold_output(self) -> float:
        silver_chest = 225
        gold_chest = 550
        half_chance_silver_or_gold = (225 + 550) / 2
        return silver_chest + gold_chest + half_chance_silver_or_gold

    @property
    def avg_shiftstone_output(self) -> float:
        total_shiftstone = 500  # flat value
        for rarity in RARITIES:
            num_cards = NUM_CARDS_IN_PACK[rarity]
            shiftstone_per_card = RARITY_REGULAR_DISENCHANT[rarity]
            shiftstone_for_rarity = num_cards * shiftstone_per_card
            total_shiftstone += (4 + self.avg_gold_chests) * shiftstone_for_rarity
        return total_shiftstone

    @property
    def avg_value(self) -> float:
        avg_value_of_draft_packs = self.num_draft_packs * self.estimated_draft_efficiency * CardPacks.draft_pack.avg_value
        avg_value_of_newest_packs = self.num_newest_packs * self.estimated_draft_efficiency * CardPacks.avg_newest_pack_value
        avg_value_of_gold_chests = self.avg_gold_chests * CardPacks.avg_golden_chest_pack_value

        avg_value = avg_value_of_draft_packs + avg_value_of_newest_packs + avg_value_of_gold_chests
        return avg_value
