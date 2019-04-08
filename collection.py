from base_learner import BaseLearner
from deck import CardPlayset
from field_hash_collection import FieldHashCollection


class PlaysetCollection(FieldHashCollection):
    def _add_to_dict(self, input: input):
        self.dict[input.set_num][input.card_num].append(input)  # dict[set_num][card_num]=objects


class CollectionLearner(BaseLearner):
    def __init__(self, file_prefix: str):
        super().__init__(file_prefix, "collection_type.json", PlaysetCollection)

    def _update_contents(self):
        try:
            with open("collection.txt", "r") as collection_file:
                collection_text = collection_file.read()
                collection_lines = collection_text.split("\n")
                for line in collection_lines:
                    playset = CardPlayset.from_export_text(line)
                    if playset is not None:
                        self.contents.append(playset)
        except FileNotFoundError:
            pass

    def _load(self):
        self.contents = PlaysetCollection()
        self._update_contents()

    def _json_entry_to_content(self, json_entry):
        pass
