from __future__ import annotations

from collections import defaultdict

from src.base_learner import BaseLearner, JsonInterface
from src.card import CardCollection
from src.deck import CardPlayset
from src.field_hash_collection import JsonLoadedCollection
from src.owned_cards import PlaysetCollection
from src.play_rate import PlayRateCollection, PlayRate


class Value:
    def __init__(self, card_name, rarity, new_count, value):
        self.card_name = card_name
        self.rarity = rarity
        self.new_count = new_count
        self.value = value

    def __float__(self):
        return self.value

    def __lt__(self, other):
        return float(self) < float(other)

    def __eq__(self, other):
        return float(self) == float(other)


class ValueCollection(JsonLoadedCollection):
    def __init__(self):
        self.deck_search = None
        super().__init__()

    def _add_to_dict(self, entry):
        self.dict["card_name"][entry.card_name].append(entry)

    @staticmethod
    def json_entry_to_content(json_entry: dict):
        pass


class ValueLearner(BaseLearner):
    def __init__(self, file_prefix,
                 owned_cards: PlaysetCollection,
                 play_rates: PlayRateCollection,
                 cards: CardCollection):
        self.owned_cards = owned_cards
        self.play_rates = play_rates
        self.cards = cards

        self.already_seen = defaultdict(bool)

        super().__init__(file_prefix, f"{self.play_rates.deck_search.name}/value.json",
                         ValueCollection)
        self._update_collection()  # todo make this better. Figure out how to handle autoupdate.

        self.collection.deck_search = self.play_rates.deck_search

    def _update_collection(self):
        for play_rate in self.play_rates.contents:
            self._update_value_from_play_rate(play_rate)

    def _update_value_from_play_rate(self, play_rate: PlayRate):
        play_rate_id = (play_rate.set_num, play_rate.card_num)
        if self.already_seen[play_rate_id]:
            return
        self.already_seen[play_rate_id] = True

        matching_playset = self._get_matching_playset(play_rate)
        if matching_playset is None:
            matching_playset = CardPlayset(play_rate.set_num, play_rate.card_num, 0)

        num_owned = matching_playset.num_played
        if num_owned >= 4:
            return

        new_count = num_owned + 1
        assert new_count in [1, 2, 3, 4]

        card_value = self._get_value(play_rate, matching_playset, new_count)

        self.collection.append(card_value)

    def _get_matching_playset(self, play_rate):
        matching_playsets = self.owned_cards.dict[play_rate.set_num][play_rate.card_num]
        if len(matching_playsets) == 0:
            return None
        return matching_playsets[0]

    def _get_value(self, play_rate, playset, new_count) -> Value:
        matching_cards = self.cards.dict[playset.set_num][
            playset.card_num]
        card = matching_cards[0]
        name = card.name
        rarity = card.rarity
        value_of_new_count = play_rate.play_rate_of_card_count[str(new_count)]
        weight = self.play_rates.deck_search.weight
        value = Value(name, rarity, new_count, weight * value_of_new_count)
        return value

    def _json_entry_to_content(self, json_entry):
        pass

    def _load(self):
        return ValueCollection()

    def _save(self):
        self.collection.contents.sort(reverse=True)
        super()._save()


class SummedValues:
    def __init__(self, file_prefix, value_collections):
        self.value_collections = value_collections
        self.json_interface = JsonInterface(file_prefix, "overall_value.json", ValueCollection)

        self.collection = self._init_collection()
        self.save()

    def _init_collection(self):
        summed_value_collection = ValueCollection()
        for value_collection in self.value_collections:
            for value in value_collection.contents:
                matching_values = summed_value_collection.dict["card_name"][value.card_name]
                if len(matching_values) > 0:
                    matching_values[0].value += value.value
                else:
                    summed_value_collection.append(value)

        return summed_value_collection

    def save(self):
        self.json_interface.save(self.collection)
