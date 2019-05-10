from eternal_collection_guide import card_pack as card_pack_mod
from eternal_collection_guide.buy_options import BuyPacks, BuyCampaigns, BuyLeague
from eternal_collection_guide.card import CardLearner
from eternal_collection_guide.draft import BuyDraft
from eternal_collection_guide.sets import Sets
from eternal_collection_guide.values import SummedValues


class BuyEfficiency:
    """Collects and exports buy options."""

    def __init__(self, file_prefix: str, card_learner: CardLearner, overall_value: SummedValues):
        self.file_prefix = file_prefix
        self.cards = card_learner
        self.value = overall_value

        self.purchase_options = self._init_purchase_options()

    def save(self):
        """Exports the purchase options to a file."""
        with open(f"{self.file_prefix}/purchases.txt", "w+") as purchase_file:
            for option in self.purchase_options:
                purchase_file.write(option.evaluation_string)

    def _init_purchase_options(self):
        sets = Sets()
        card_packs = card_pack_mod.CardPacks(sets, self.cards.collection, self.value.collection)

        print("Getting card packs")
        buy_packs = BuyPacks(sets, self.cards.collection, self.value.collection)

        print("Getting campaigns")
        buy_campaigns = BuyCampaigns(sets, self.cards.collection, self.value.collection)

        purchase_options = buy_packs.contents + buy_campaigns.contents

        print("Getting draft")
        purchase_options.append(BuyDraft(card_packs))

        print("Getting league")
        purchase_options.append(BuyLeague(card_packs))
        purchase_options = sorted(purchase_options, reverse=True)
        return purchase_options
