from src.base_learner import BaseLearner
from src.deck import CardPlayset
from src.field_hash_collection import JsonLoadedCollection


class PlaysetCollection(JsonLoadedCollection):
    def _add_to_dict(self, entry: any):
        self.dict[entry.set_num][entry.card_num].append(entry)  # dict[set_num][card_num]=objects

    @staticmethod
    def json_entry_to_content(json_entry: dict):
        pass


class OwnedCardsLearner(BaseLearner):
    def __init__(self, file_prefix: str):
        super().__init__(file_prefix, "owned_cards.json", PlaysetCollection)
        self.update()  # todo improve autoupdate

    def _update_collection(self):
        try:
            with open("collection.txt", "r") as collection_file:
                collection_text = collection_file.read()
                collection_lines = collection_text.split("\n")
                for line in collection_lines:
                    playset = CardPlayset.from_export_text(line)
                    if playset is not None:
                        matches = self.collection.dict[playset.set_num][playset.card_num]
                        if len(matches) > 0:
                            existing_playset = matches[0]
                            existing_playset.num_played += playset.num_played
                        else:
                            self.collection.append(playset)
        except FileNotFoundError:
            print("collection.txt not found")

    def _load(self):
        return PlaysetCollection()

    def update(self):
        self._update_collection()
        self._save()
