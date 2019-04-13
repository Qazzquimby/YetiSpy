from card import CardLearner
from deck import DeckLearner
from deck_searches import get_deck_searches
from owned_cards import OwnedCardsLearner
from play_rate import PlayRateLearner
from value import ValueLearner, SummedValues

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
        value_learner.update()
        values.append(value_learner.collection)

    overall_value = SummedValues(file_prefix, values)
