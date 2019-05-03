from __future__ import annotations

import re
import typing
from dataclasses import dataclass

from eternal_collection_guide.base_learner import BaseLearner
from eternal_collection_guide.field_hash_collection import FieldHashCollection


@dataclass
class Playset:
    """A quantity of a given card."""
    set_num: int
    card_num: int
    num_copies: int

    def __str__(self):
        return f"{self.num_copies}x {self.set_num}-{self.card_num}"

    @classmethod
    def from_export_text(cls, text) -> typing.Optional[Playset]:
        """Creates a playset from a row of a deck or collection export.

        :param text: A single row of the export.
        :return: A playset representing the card on that row.
        """
        numbers = [int(number) for number in re.findall(r'\d+', text)]
        if len(numbers) == 3:
            num_played = numbers[0]
            set_num = numbers[1]
            card_num = numbers[2]
            playset = Playset(set_num, card_num, num_played)
            return playset
        return None


class PlaysetCollection(FieldHashCollection[Playset]):
    """A collection of cards and their quantities.

    self.dict[<set_num>][<card_num>] = list of playsets
    """

    def _add_to_dict(self, entry: any):
        self.dict[entry.set_num][entry.card_num].append(entry)  # dict[set_num][card_num]=objects


class OwnedCardsLearner(BaseLearner):
    """Populates a PlaysetCollection from the contents of collection.txt"""

    def __init__(self, file_prefix: str):
        self.collection_path = "../collection.txt"
        super().__init__(file_prefix, "owned_cards.json", PlaysetCollection, dependent_paths=[self.collection_path])

    def update(self):
        self._update_collection()
        # Don't save. Inexpensive to rebuild.

    def _is_old(self):
        return True  # Inexpensive to rebuild, so always update

    def _update_collection(self):
        try:
            with open(self.collection_path, "r") as collection_file:
                collection_text = collection_file.read()
                collection_lines = collection_text.split("\n")
                for line in collection_lines:
                    playset = Playset.from_export_text(line)
                    if playset is not None:
                        matches = self.collection.dict[playset.set_num][playset.card_num]
                        if len(matches) > 0:
                            existing_playset = matches[0]  # type: Playset
                            existing_playset.num_copies += playset.num_copies
                        else:
                            self.collection.append(playset)
        except FileNotFoundError:
            print("collection.txt not found")

    def _load(self) -> PlaysetCollection:
        return self.json_interface.load_empty()
