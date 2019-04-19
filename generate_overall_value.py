from eternal_collection_guide.card import CardLearner
from eternal_collection_guide.deck import DeckLearner
from eternal_collection_guide.deck_searches import get_deck_searches
from eternal_collection_guide.owned_cards import OwnedCardsLearner
from eternal_collection_guide.play_rate import PlayRateLearner
from eternal_collection_guide.purchase_options import BuyPacks
from eternal_collection_guide.sets import Sets
from eternal_collection_guide.values import ValueLearner, SummedValues

file_prefix = "output"

if __name__ == '__main__':
    card_learner = CardLearner(file_prefix)
    # card_learner.update()

    deck_searches = get_deck_searches()
    values = []
    for deck_search in deck_searches:
        deck_learner = DeckLearner(file_prefix, deck_search)
        # deck_learner.update()

        owned_cards_learner = OwnedCardsLearner(file_prefix)

        card_play_rates = PlayRateLearner(file_prefix,
                                          card_learner.collection,
                                          deck_learner.collection)

        value_learner = ValueLearner(file_prefix, owned_cards_learner.collection,
                                     card_play_rates.collection,
                                     card_learner.collection)
        values.append(value_learner.collection)

    overall_value = SummedValues(file_prefix, values)

    sets = Sets()

    buy_packs = BuyPacks(sets, card_learner.collection, overall_value.collection)
    for pack in buy_packs:
        print(pack.card_pack.set_num, pack.avg_value)
    pass
