from __future__ import annotations

import typing
from collections import defaultdict
from dataclasses import dataclass

from eternal_collection_guide.base_learner import BaseLearner, JsonInterface
from eternal_collection_guide.card import CardCollection
from eternal_collection_guide.deck import Playset
from eternal_collection_guide.deck_searches import DeckSearch
from eternal_collection_guide.field_hash_collection import JsonLoadedCollection
from eternal_collection_guide.owned_cards import PlaysetCollection
from eternal_collection_guide.play_rate import PlayRateCollection, PlayRate
from eternal_collection_guide.rarities import Rarity
from eternal_collection_guide.shiftstone import RARITY_REGULAR_ENCHANT


@dataclass(frozen=True)
class ValueSet:
    """The values of each unowned copy of a card."""
    card_name: str
    rarity: Rarity
    num_owned: int
    values: typing.List[float]

    @property
    def value_per_100_shiftstone(self):
        """Gives the effective value of crafting the card."""
        return self.values[0] * 100 / RARITY_REGULAR_ENCHANT[self.rarity]

    def __float__(self):
        try:
            return self.values[0]
        except IndexError:
            return 0

    def __lt__(self, other):
        return float(self) < float(other)

    def __eq__(self, other):
        return float(self) == float(other)


class ValueCollection(JsonLoadedCollection):
    def __init__(self):
        self.deck_search: typing.Optional[DeckSearch] = None
        self._contents: ValueSet
        super().__init__()

    def _add_to_dict(self, entry):
        self.dict["card_name"][entry.card_name].append(entry)

    @staticmethod
    def json_entry_to_content(json_entry: dict) -> None:
        pass


class ValueLearner(BaseLearner):
    def __init__(self, file_prefix: str,
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
        self._save()
        self.collection.deck_search = self.play_rates.deck_search

    def update(self):
        pass  # automatic

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

        num_owned = owned_playset.num_copies
        if num_owned >= 4:
            return

        assert num_owned in [0, 1, 2, 3]

        card_value = self._get_values(play_rate, owned_playset, num_owned)

        self.collection.append(card_value)

    def _get_owned_playset(self, play_rate: PlayRate) -> typing.Optional[PlayRate]:
        owned_playsets = self.owned_cards.dict[play_rate.set_num][play_rate.card_num]
        if len(owned_playsets) == 0:
            return None
        return owned_playsets[0]

    def _get_values(self, play_rate: PlayRate, owned: Playset, num_owned: int) -> ValueSet:
        card = self.cards.dict[owned.set_num][owned.card_num][0]

        values = [play_rate.play_rate_of_card_count[str(card_count)] for card_count in range(num_owned + 1, 5)]

        values = ValueSet(card.name, card.rarity, num_owned, values)
        return values

    def _load(self) -> ValueCollection:
        return ValueCollection()

    def _save(self):
        self.collection.sort(reverse=True)
        super()._save()


class SummedValues:
    def __init__(self, file_prefix, value_collections: typing.List[ValueCollection]):
        self.value_collections = value_collections
        self.json_interface = JsonInterface(file_prefix, "overall_value.json", ValueCollection)
        self.json_interface_by_shiftstone = JsonInterface(file_prefix, 'overall_value_by_shiftstone.json',
                                                          ValueCollection)

        self.collection = self._init_collection()
        self.save()

    def _init_collection(self) -> ValueCollection:
        summed_value_collection = ValueCollection()

        total_weight = 0
        for value_collection in self.value_collections:
            current_weight = value_collection.deck_search.weight
            total_weight += current_weight
            for value_set in value_collection.contents:
                matching_value_sets = summed_value_collection.dict["card_name"][value_set.card_name]
                if len(matching_value_sets) > 0:
                    matching_value_set: ValueSet = matching_value_sets[0]
                    weight_difference = total_weight - current_weight
                    old_values = [value * weight_difference / total_weight for value in matching_value_set.values]
                    new_values = [value * current_weight / total_weight for value in value_set.values]
                    averaged_values = [old + new for old, new in zip(old_values, new_values)]

                    matching_value_set.values = averaged_values
                else:
                    summed_value_collection.append(value_set)

        return summed_value_collection

    def save(self):
        self.collection.sort(reverse=True)
        self.json_interface.save(self.collection)

        def get_value_per_100_shiftstone(value: ValueSet):
            return value.value_per_100_shiftstone

        self.collection.sort(key=get_value_per_100_shiftstone, reverse=True)
        self.json_interface_by_shiftstone.save(self.collection)
