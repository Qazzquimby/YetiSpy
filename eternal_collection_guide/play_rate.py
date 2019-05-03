from eternal_collection_guide.base_learner import JsonCompatible, DeckSearchLearner
from eternal_collection_guide.card import CardLearner
from eternal_collection_guide.deck import DeckLearner
from eternal_collection_guide.field_hash_collection import FieldHashCollection


class PlayRate(JsonCompatible):
    """The amount a quanitity of a card is used in a set of decks."""

    def __init__(self, set_num: int, card_num: int):
        self.set_num = set_num
        self.card_num = card_num
        self.play_rate_of_card_count = {'1': 0, '2': 0, '3': 0, '4': 0}

    def __str__(self):
        return f"{self.set_num}-{self.card_num}: {self.play_rate_of_card_count[str(0)]}, " \
            f"{self.play_rate_of_card_count[str(2)]}, " \
            f"{self.play_rate_of_card_count[str(3)]}, " \
            f"{self.play_rate_of_card_count[str(4)]}"

    @classmethod
    def from_json(cls, entry: dict):
        """Constructs a Deck from a json_entry representing a deck.

        :param entry:
        :return:
        """
        result = cls(entry['set_num'], entry['card_num'])
        result.play_rate_of_card_count = entry['play_rate_of_card_count']

        return result


class PlayRateCollection(FieldHashCollection[PlayRate]):
    """A collection of PlayRates

    self.dict[<set_num>][<card_num>] = list of PlayRates.
    """
    content_type = PlayRate

    def __init__(self):
        self.deck_search = None  # fixme
        super().__init__()

    def _add_to_dict(self, entry: any):
        self.dict[entry.set_num][entry.card_num].append(entry)


class PlayRateLearner(DeckSearchLearner):
    """Populates a PlayRateCollection from an EternalWarcry deck search."""

    def __init__(self, file_prefix: str,
                 card_learner: CardLearner,
                 deck_learner: DeckLearner):
        self.cards = card_learner
        self.decks = deck_learner

        dependent_paths = [self.cards.json_interface.path,
                           self.decks.json_interface.path]

        super().__init__(file_prefix, f"{self.decks.deck_search.name}/play_rates.json",
                         PlayRateCollection,
                         self.decks.deck_search,
                         dependent_paths=dependent_paths)

    def _update_collection(self):
        self.collection = self.json_interface.load_empty()

        for card in self.cards.collection.contents:
            play_rate = PlayRate(card.set_num, card.card_num)
            for num_played in range(1, 5):
                decks_with_num_played = self.decks.collection.dict[(card.set_num, card.card_num)][num_played]
                num_played_play_count = len(decks_with_num_played)
                play_rate.play_rate_of_card_count[str(num_played)] += \
                    num_played_play_count

            num_decks = len(self.decks.collection.contents)
            for num_played in range(1, 5):
                try:
                    play_rate.play_rate_of_card_count[str(num_played)] *= 100 / num_decks
                except ZeroDivisionError:
                    pass

            if play_rate.play_rate_of_card_count['1'] > 0:  # used at least once
                self.collection.append(play_rate)
