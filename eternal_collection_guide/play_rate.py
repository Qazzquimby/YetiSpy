from eternal_collection_guide.base_learner import BaseLearner, JsonCompatible
from eternal_collection_guide.card import CardCollection
from eternal_collection_guide.deck import DeckCollection
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


class PlayRateLearner(BaseLearner):
    """Populates a PlayRateCollection from an EternalWarcry deck search."""

    def __init__(self, file_prefix: str,
                 card_collection: CardCollection,
                 deck_collection: DeckCollection):
        self.cards = card_collection
        self.decks = deck_collection

        super().__init__(file_prefix, f"{self.decks.deck_search.name}/play_rates.json",
                         PlayRateCollection)

        self.collection.deck_search = self.decks.deck_search

        self._update_collection()
        self._save()

    def update(self):
        pass  # updates automatically

    def _load(self) -> PlayRateCollection:
        return self.json_interface.load_empty()  # todo properly remake

    def _update_collection(self):
        for card in self.cards.contents:
            play_rate = PlayRate(card.set_num, card.card_num)
            for num_played in range(1, 5):
                decks_with_num_played = self.decks.dict[(card.set_num, card.card_num)][num_played]
                num_played_play_count = len(decks_with_num_played)
                play_rate.play_rate_of_card_count[str(num_played)] += \
                    num_played_play_count

            num_decks = len(self.decks.contents)
            for num_played in range(1, 5):
                try:
                    play_rate.play_rate_of_card_count[str(num_played)] *= 100 / num_decks
                except ZeroDivisionError:
                    pass

            if play_rate.play_rate_of_card_count['1'] > 0:  # used at least once
                self.collection.append(play_rate)
