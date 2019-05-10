from eternal_collection_guide.file_prefix import file_prefix
from . import buy_efficiency
from .card import CardLearner
from .deck import DeckLearner
from .deck_searches import get_deck_searches
from .owned_cards import OwnedCardsLearner
from .play_rate import PlayRateLearner
from .values import ValueLearner, SummedValues

if __name__ == '__main__':
    card_learner = CardLearner(file_prefix)
    owned_cards_learner = OwnedCardsLearner(file_prefix)

    deck_searches = get_deck_searches()
    values = []
    for deck_search in deck_searches:
        deck_learner = DeckLearner(file_prefix, deck_search, card_learner)

        card_play_rates = PlayRateLearner(file_prefix, card_learner, deck_learner)

        value_learner = ValueLearner(file_prefix, owned_cards_learner, card_play_rates, card_learner)
        values.append(value_learner.collection)

    overall_value = SummedValues(file_prefix, values)

    purchase_efficiency = buy_efficiency.BuyEfficiency(file_prefix, card_learner, overall_value).save()
