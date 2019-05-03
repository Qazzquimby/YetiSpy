"""Related to the Draft purchase option in Eternal"""
from eternal_collection_guide.card_pack import CardPacks
from eternal_collection_guide.purchase_options import BuyOption
from eternal_collection_guide.rarities import RARITIES
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT


class BuyDraft(BuyOption):
    """A purchase of a Draft run in Eternal."""

    def __init__(self, card_packs: CardPacks):
        self.card_packs = card_packs

        super().__init__()

        self._num_newest_packs = 2
        self._num_draft_packs = 2

        self._avg_wins = 2.4  # statistical average is ~2.8. This is slightly lower to account for collection-drafting.
        self._avg_gold_chests = self._avg_wins - 1  # only works if avg_wins between 2 and 4
        self._estimated_draft_efficiency = 1.25

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
            total_shiftstone += (4 + self._avg_gold_chests) * shiftstone_for_rarity
        return total_shiftstone

    @property
    def avg_value(self) -> float:
        return self._value_of_draft_packs() + self._value_of_newest_packs() + self._value_of_gold_chests()

    def _value_of_draft_packs(self):
        value_of_draft_pack = self._estimated_draft_efficiency * self.card_packs.draft_pack.avg_value
        value_of_draft_packs = self._num_draft_packs * value_of_draft_pack
        return value_of_draft_packs

    def _value_of_newest_packs(self):
        value_of_newest_pack = self._estimated_draft_efficiency * self.card_packs.avg_newest_pack_value
        value_of_newest_packs = self._num_newest_packs * value_of_newest_pack
        return value_of_newest_packs

    def _value_of_gold_chests(self):
        return self._avg_gold_chests * self.card_packs.avg_golden_chest_pack_value
