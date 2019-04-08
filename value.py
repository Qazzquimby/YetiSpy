from __future__ import annotations

from collections import defaultdict

from base_learner import BaseLearner
from card import CardCollection
from collection import CardPlaysetCollection
from field_hash_collection import FieldHashCollection
from play_rate import CardCountPlayRateCollection, CardCountPlayRate


class Value(object):
    def __init__(self, card_name, rarity, new_count, play_rate):
        self.card_name = card_name
        self.rarity = rarity
        self.new_count = new_count
        self.play_rate = play_rate

    def __int__(self):
        return self.play_rate

    def __lt__(self, other):
        return int(self) < int(other)

    def __eq__(self, other):
        return int(self) == int(other)


class ValueCollection(FieldHashCollection):
    def _add_to_dict(self, input: input):
        self.dict["card_name"][input.card_name].append(input)


class ValueLearner(BaseLearner):
    def __init__(self, file_prefix,
                 collection: CardPlaysetCollection,
                 play_rates: CardCountPlayRateCollection,
                 cards: CardCollection):
        self.collection = collection
        self.play_rates = play_rates
        self.cards = cards

        self.already_seen = defaultdict(bool)

        super().__init__(file_prefix, "value.json", ValueCollection)

    def _update_contents(self):
        for play_rate in self.play_rates.contents:
            self._update_value_from_play_rate(play_rate)

    def _update_value_from_play_rate(self, play_rate: CardCountPlayRate):
        play_rate_id = (play_rate.set_num, play_rate.card_num)
        if self.already_seen[play_rate_id]:
            return
        self.already_seen[play_rate_id] = True

        matching_playset = self._get_matching_playset(play_rate)
        if matching_playset is None:
            return

        num_owned = matching_playset.num_played
        if num_owned >= 4:
            return

        new_count = num_owned + 1
        assert new_count in [1, 2, 3, 4]

        card_value = self._get_card_value(play_rate, matching_playset, new_count)

        self.contents.append(card_value)

    def _get_matching_playset(self, play_rate):
        matching_playsets = self.collection.dict[play_rate.set_num][play_rate.card_num]
        if len(matching_playsets) == 0:
            return None
        else:
            return matching_playsets[0]

    def _get_card_value(self, play_rate, playset, new_count) -> Value:
        matching_cards = self.cards.dict[playset.set_num][
            playset.card_num]
        card = matching_cards[0]
        name = card.name
        rarity = card.rarity
        value_of_new_count = play_rate.play_rate_of_card_count[str(new_count)]
        card_value = Value(name, rarity, new_count, value_of_new_count)
        return card_value

    def _json_entry_to_content(self, json_entry):
        pass

    def _load(self):
        self.contents = ValueCollection()
        self._update_contents()

    def _save(self):
        self.contents.contents = sorted(self.contents.contents, reverse=True)
        super()._save()
