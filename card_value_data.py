from __future__ import annotations

from base_learner import BaseLearner
from field_hash_collection import FieldHashCollection


class CardValueData(object):
    def __init__(self, card_name, new_count, play_rate):
        self.card_name = card_name
        self.new_count = new_count
        self.play_rate = play_rate

    def __int__(self):
        return self.play_rate


class CardValueCollection(FieldHashCollection):
    def _add_to_dict(self, input: input):
        self.dict["card_name"][input.card_name].append(input)


class CardValueLearner(BaseLearner):
    def __init__(self, file_prefix, collection, play_rates):
        self.collection = collection
        self.play_rates = play_rates

        super().__init__(file_prefix, "value.json", CardValueCollection)

    def _update_contents(self):
        pass

    def _json_entry_to_content(self, json_entry):
        pass
