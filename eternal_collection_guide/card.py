"""Objects related to Cards in Eternal"""
import json
import typing
from dataclasses import dataclass

from progiter import progiter

from eternal_collection_guide.base_learner import BaseLearner, JsonCompatible
from eternal_collection_guide.browser import Browser
from eternal_collection_guide.field_hash_collection import FieldHashCollection
from eternal_collection_guide.rarities import RARITIES


@dataclass
class Card(JsonCompatible):
    """Represents a card in Eternal"""
    set_num: int
    card_num: int
    name: str
    rarity: str

    def __str__(self):
        return f"{self.name} - {self.set_num}, {self.card_num}"


class CardCollection(FieldHashCollection[Card]):
    """A searchable collection of Cards.

    self.dict[<set_num>][<card_num] = a list of matching cards.
    self.dict["name"][<name>] = a list of cards with that name.
    """
    content_type = Card

    def get_cards_in_set(self, set_num: int) -> typing.List[Card]:
        """Return a list of cards in the given set.

        Set 0 and 1 are both found under set 1.
        """
        if set_num == 0:
            raise ValueError("Cannot use set_num 0. Use set_num 1 to refer to both 0 and 1.")

        if set_num == 1:
            return self._get_cards_in_set(0) + self._get_cards_in_set(1)
        return self._get_cards_in_set(set_num)

    def _get_cards_in_set(self, set_num: int) -> typing.List[Card]:

        cards = []

        card_nums_in_set = self.dict[set_num]
        for card_num in card_nums_in_set.keys():
            new_cards = self.dict[set_num][card_num]
            if len(new_cards) > 0:
                card = new_cards[0]
                cards.append(card)
        return cards

    def _add_to_dict(self, entry: any):
        self.dict[entry.set_num][entry.card_num].append(entry)  # dict[set_num][card_num]=objects
        self.dict["name"][entry.name].append(entry)  # dict["name"][name]=objects


def get_card_num_from_card_url(url: str) -> int:
    """Gets a card's number from its Eternal Warcry details url."""
    set_card_string = _get_set_card_string_from_card_url(url)
    card_num = int(set_card_string.split("-")[1])
    return card_num


def get_set_num_from_card_url(url: str) -> int:
    """Gets a card's set number from its Eternal Warcry details url."""
    set_card_string = _get_set_card_string_from_card_url(url)
    set_num = int(set_card_string.split("-")[0])
    return set_num


def _get_set_card_string_from_card_url(url: str) -> str:
    base_url = 'https://eternalwarcry.com/cards/details/'
    url = url.replace(base_url, "")
    set_card_string = url.split("/")[0]
    return set_card_string


class CardLearner(BaseLearner):
    """Populates a card collection from the card database at Eternal Warcry."""

    def __init__(self, file_prefix: str):
        super().__init__(file_prefix, "cards.json", CardCollection, max_days_before_update=30)

    def _update_collection(self):
        card_json = self._get_card_json()
        entries = json.loads(card_json)
        self.collection = self._make_collection_from_export_entries(entries)

    @staticmethod
    def _get_card_json():
        with Browser() as browser:
            browser.get("https://eternalwarcry.com/content/cards/eternal-cards.json")
            element = browser.safely_find(lambda x: x.find_element_by_xpath("/html/body/pre"))
            card_json = element.text
        return card_json

    @staticmethod
    def _make_collection_from_export_entries(entries: typing.List[dict]) -> CardCollection:
        collection = CardCollection()
        for entry in progiter.ProgIter(entries):
            card = CardLearner._make_card_from_export_entry(entry)
            if card is not None:
                collection.append(card)
        return collection

    @staticmethod
    def _make_card_from_export_entry(entry: dict) -> typing.Optional[Card]:
        try:
            if not entry["DeckBuildable"]:
                return None
            if entry["Rarity"].lower() not in RARITIES:
                return None

            content = Card(entry['SetNumber'],
                           entry['EternalID'],
                           entry['Name'],
                           entry['Rarity'].lower())
            return content
        except KeyError:
            return None
