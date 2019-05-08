from eternal_collection_guide.card import CardLearner
from eternal_collection_guide.card_pack import CardPacks
from eternal_collection_guide.deck import DeckLearner
from eternal_collection_guide.deck_searches import get_deck_searches
from eternal_collection_guide.draft import BuyDraft
from eternal_collection_guide.owned_cards import OwnedCardsLearner
from eternal_collection_guide.play_rate import PlayRateLearner
from eternal_collection_guide.purchase_options import BuyPacks, BuyCampaigns, BuyCampaign, BuyPack, BuyLeague, BuyOption
from eternal_collection_guide.sets import Sets
from eternal_collection_guide.values import ValueLearner, SummedValues

file_prefix = "output"


def purchase_efficiency_string(purchase: BuyOption):
    return f"  -  Value per 1000 gold = {purchase.avg_value_per_1000_gold}" \
        f"  -  Value per 100 gems = {purchase.avg_value_per_100_gems}\n"


if __name__ == '__main__':
    card_learner = CardLearner(file_prefix)
    owned_cards_learner = OwnedCardsLearner(file_prefix)
    # card_learner.update())

    deck_searches = get_deck_searches()
    values = []
    for deck_search in deck_searches:
        deck_learner = DeckLearner(file_prefix, deck_search, card_learner)
        # deck_learner.update()

        card_play_rates = PlayRateLearner(file_prefix,
                                          card_learner,
                                          deck_learner)

        value_learner = ValueLearner(file_prefix, owned_cards_learner,
                                     card_play_rates,
                                     card_learner)
        values.append(value_learner.collection)

    overall_value = SummedValues(file_prefix, values)

    sets = Sets()
    card_packs = CardPacks(sets, card_learner.collection, overall_value.collection)

    buy_packs = BuyPacks(sets, card_learner.collection, overall_value.collection)
    buy_campaigns = BuyCampaigns(sets, card_learner.collection, overall_value.collection)

    purchase_options = buy_packs.contents + buy_campaigns.contents
    purchase_options.append(BuyDraft(card_packs))
    purchase_options.append(BuyLeague(card_packs))
    purchase_options = sorted(purchase_options, reverse=True)

    with open(f"{file_prefix}/purchases.txt", "w+") as purchase_file:
        for option in purchase_options:
            if type(option) is BuyCampaign:
                # noinspection PyUnresolvedReferences
                purchase_file.write(f"Buy campaign: {option.content.name}" + purchase_efficiency_string(option))
            if type(option) is BuyPack:
                # noinspection PyUnresolvedReferences
                purchase_file.write(f"Buy pack: {option.content.name}" + purchase_efficiency_string(option))
            if type(option) is BuyDraft:
                # noinspection PyUnresolvedReferences
                purchase_file.write(f"Buy Draft" + purchase_efficiency_string(option))
            if type(option) is BuyLeague:
                # noinspection PyUnresolvedReferences
                purchase_file.write(f"Buy League" + purchase_efficiency_string(option))
