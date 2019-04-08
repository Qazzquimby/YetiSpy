from base_learner import BaseLearner
from card_data import CardCollection
from deck_data import DeckCollection
from field_hash_collection import FieldHashCollection


class CardPlayRateLearner(BaseLearner):
    def __init__(self, file_prefix: str,
                 card_collection: CardCollection,
                 deck_collection: DeckCollection):
        self.cards = card_collection
        self.decks = deck_collection

        super().__init__(file_prefix, "play_rates.json", CardCountPlayRateCollection)

    def _load(self):
        if self.cards.updated or self.decks.updated:
            self.contents = self.collection_type()
            self.update()
        else:
            super()._load()

    def _update_contents(self):

        for card in self.cards.contents:
            card_count_play_rate = CardCountPlayRate(card.set_num, card.card_num)
            for num_played in range(1, 5):
                decks_with_num_played = self.decks.dict[(card.set_num, card.card_num)][num_played]
                num_played_play_count = len(decks_with_num_played)
                card_count_play_rate.play_rate_of_card_count[num_played] += num_played_play_count

            if card_count_play_rate.play_rate_of_card_count[1] > 0:
                self.contents.append(card_count_play_rate)

    def _json_entry_to_content(self, json_entry):
        pass


class CardCountPlayRate(object):
    def __init__(self, set_num: int, card_num: int):
        self.set_num = set_num
        self.card_num = card_num
        self.play_rate_of_card_count = {1: 0, 2: 0, 3: 0, 4: 0}

    def __str__(self):
        return f"{self.set_num}-{self.card_num}: {self.play_rate_of_card_count[0]}, " \
            f"{self.play_rate_of_card_count[2]}, " \
            f"{self.play_rate_of_card_count[3]}, " \
            f"{self.play_rate_of_card_count[4]}"


class CardCountPlayRateCollection(FieldHashCollection):
    def _add_to_dict(self, input: input):
        self.dict[input.set_num][input.card_num].append(input)
