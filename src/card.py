import json
import typing
from dataclasses import dataclass

from src.base_learner import BaseLearner
from src.browser import Browser
from src.field_hash_collection import JsonLoadedCollection
from src.progress_printer import ProgressPrinter


@dataclass
class Rarity:
    id: str
    name: str


COMMON = "common"
UNCOMMON = "uncommon"
RARE = "rare"
LEGENDARY = "legendary"
PROMO = "promo"

RARITIES = [COMMON, UNCOMMON, RARE, LEGENDARY, PROMO]

rarity_string_to_id = {COMMON: 2,
                       UNCOMMON: 3,
                       RARE: 4,
                       LEGENDARY: 5,
                       PROMO: 6}


class Card:
    def __init__(self, set_num: int, card_num: int, name: str, rarity: str):
        self.set_num = set_num
        self.card_num = card_num
        self.name = name
        self.rarity = rarity

    def __str__(self):
        return f"{self.name} - {self.set_num}, {self.card_num}"


class CardCollection(JsonLoadedCollection):

    @staticmethod
    def json_entry_to_content(json_entry: dict) -> Card:
        content = Card(json_entry['set_num'],
                       json_entry['card_num'],
                       json_entry['name'],
                       json_entry['rarity'])
        return content

    def _add_to_dict(self, entry: any):
        self.dict[entry.set_num][entry.card_num].append(entry)  # dict[set_num][card_num]=objects
        self.dict["name"][entry.name].append(entry)  # dict["name"][name]=objects


def get_set_card_string_from_card_url(url: str) -> str:
    base_url = 'https://eternalwarcry.com/cards/details/'
    url = url.replace(base_url, "")
    set_card_string = url.split("/")[0]
    return set_card_string


def get_card_num_from_card_url(url: str) -> int:
    set_card_string = get_set_card_string_from_card_url(url)
    card_num = int(set_card_string.split("-")[1])
    return card_num


def get_set_num_from_card_url(url: str) -> int:
    set_card_string = get_set_card_string_from_card_url(url)
    set_num = int(set_card_string.split("-")[0])
    return set_num


class CardLearner(BaseLearner):
    def __init__(self, file_prefix: str):
        super().__init__(file_prefix, "cards.json", CardCollection)
        self.progress_printer = ProgressPrinter("Updating cards", 25, 5)

    def _update_collection(self):
        card_json = self._get_card_json()
        entries = json.loads(card_json)
        self.collection = self._make_collection_from_export_entries(entries)

    @staticmethod
    def _get_card_json():
        with Browser() as browser:
            browser.get("https://eternalwarcry.com/content/cards/eternal-cards.json")
            element = browser.find_element_by_xpath("/html/body/pre")
            card_json = element.text
        return card_json

    @staticmethod
    def _make_collection_from_export_entries(entries: typing.List[dict]) -> CardCollection:
        collection = CardCollection()
        for entry in entries:
            card = CardLearner._make_card_from_export_entry(entry)
            if card is not None:
                collection.append(card)
        return collection

    @staticmethod
    def _make_card_from_export_entry(entry: dict) -> typing.Optional[Card]:
        try:
            if not entry["DeckBuildable"]:
                return None

            content = Card(entry['SetNumber'],
                           entry['EternalID'],
                           entry['Name'],
                           entry['Rarity'].lower())
            return content
        except KeyError:
            return None
