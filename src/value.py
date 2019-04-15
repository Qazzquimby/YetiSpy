from __future__ import annotations

import typing
from collections import defaultdict

from src.base_learner import BaseLearner, JsonInterface
from src.card import CardCollection
from src.deck import Playset
from src.deck_searches import DeckSearch
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
        self.deck_search = None  # type: typing.Optional[DeckSearch]
        super().__init__()

    def _add_to_dict(self, entry):
        self.dict["card_name"][entry.card_name].append(entry)

    @staticmethod
    def json_entry_to_content(json_entry: dict):
        pass


class PlayRateNormalizer:
    # todo remove. Instead make play rate show the percentage of decks used in, rather than total num
    def __init__(self, play_rates: typing.List[PlayRate]):
        self.total_cards_played = self._init_total_cards_played(play_rates)

    def normalize_play_rate(self, play_rate: float) -> float:
        normalized = play_rate * 4 * 75 / self.total_cards_played
        return normalized

    # noinspection PyMethodMayBeStatic
    def _init_total_cards_played(self, play_rates: typing.List[PlayRate]) -> int:
        total_cards = 0
        for play_rate in play_rates:
            for i in range(1, 5):
                num_cards = play_rate.play_rate_of_card_count[str(i)]
                total_cards += num_cards
        return total_cards


class ValueLearner(BaseLearner):
    def __init__(self, file_prefix,
                 owned_cards: PlaysetCollection,
                 play_rates: PlayRateCollection,
                 cards: CardCollection):
        self.owned_cards = owned_cards
        self.play_rates = play_rates
        self.cards = cards

        self.already_seen = defaultdict(bool)
        self.play_rate_normalizer = PlayRateNormalizer(self.play_rates.contents)

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

        owned_playset = self._get_owned_playset(play_rate)
        if owned_playset is None:
            owned_playset = Playset(play_rate.set_num, play_rate.card_num, 0)

        num_owned = owned_playset.num_played
        if num_owned >= 4:
            return

        new_count = num_owned + 1
        assert new_count in [1, 2, 3, 4]

        card_value = self._get_value(play_rate, owned_playset, new_count)

        self.collection.append(card_value)

    def _get_owned_playset(self, play_rate: PlayRate):
        owned_playsets = self.owned_cards.dict[play_rate.set_num][play_rate.card_num]
        if len(owned_playsets) == 0:
            return None
        return owned_playsets[0]

    def _get_value(self, play_rate: PlayRate, owned: Playset, new_count: int) -> Value:
        card = self.cards.dict[owned.set_num][owned.card_num][0]

        rate = play_rate.play_rate_of_card_count[str(new_count)]

        value = Value(card.name, card.rarity, new_count, rate)
        return value

    def _load(self):
        return ValueCollection()

    def _save(self):
        self.collection.sort(reverse=True)
        super()._save()


class SummedValues:
    def __init__(self, file_prefix, value_collections: typing.List[ValueCollection]):
        self.value_collections = value_collections
        self.json_interface = JsonInterface(file_prefix, "overall_value.json", ValueCollection)

        self.collection = self._init_collection()
        self.save()

    def _init_collection(self):
        summed_value_collection = ValueCollection()

        total_weight = 0
        for value_collection in self.value_collections:
            current_weight = value_collection.deck_search.weight
            total_weight += current_weight
            for value in value_collection.contents:
                matching_values = summed_value_collection.dict["card_name"][value.card_name]
                if len(matching_values) > 0:
                    matching_value = matching_values[0]
                    weight_difference = total_weight - current_weight
                    old_values = matching_value.value * weight_difference / total_weight
                    new_value = value.value * current_weight / total_weight
                    averaged_values = old_values + new_value

                    matching_value.value = averaged_values
                else:
                    summed_value_collection.append(value)

        return summed_value_collection

    def save(self):
        self.collection.sort(reverse=True)
        self.json_interface.save(self.collection)
