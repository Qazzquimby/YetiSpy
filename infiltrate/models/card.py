"""The Card model and related utilities

Related to card_collections.py
"""
import json
import typing
from dataclasses import dataclass
from typing import NamedTuple

from finisher import DictStorageAutoCompleter

from infiltrate import browser
from infiltrate import db
from infiltrate import models


class Card(db.Model):
    """Model representing an Eternal card."""
    __tablename__ = "cards"
    set_num = db.Column("SetNumber", db.Integer, primary_key=True)
    card_num = db.Column("EternalID", db.Integer, primary_key=True)
    name = db.Column("Name", db.String(length=40), unique=True, nullable=False)
    rarity = db.Column("Rarity", db.String(length=9), db.ForeignKey("rarities.Name"), nullable=False)
    image_url = db.Column("ImageUrl", db.String(length=100), unique=True, nullable=False)
    details_url = db.Column("DetailsUrl", db.String(length=100), unique=True, nullable=False)


def _get_card_json():
    card_json_str = browser.get_str_from_url_and_xpath("https://eternalwarcry.com/content/cards/eternal-cards.json",
                                                       "/html/body/pre")
    card_json = json.loads(card_json_str)
    return card_json


def _make_cards_from_entries(entries: typing.List[dict]):
    for entry in entries:
        _make_card_from_entry(entry)


def _make_card_from_entry(entry: dict) -> typing.Optional[Card]:
    if not entry["DeckBuildable"] or entry["Rarity"] == 'None':
        return
    card = Card(set_num=entry["SetNumber"],
                card_num=entry["EternalID"],
                name=entry["Name"],
                rarity=entry["Rarity"],
                image_url=entry["ImageUrl"],
                details_url=entry["DetailsUrl"])
    db.session.merge(card)


def update_cards():
    """Updates the db to match the Warcry cards list."""
    card_json = _get_card_json()
    _make_cards_from_entries(card_json)
    db.session.commit()


class CardId(NamedTuple):
    """A key to identify a card."""
    set_num: int
    card_num: int


class CardPlayset(NamedTuple):
    """Multiple copies of a card"""
    card_id: CardId
    count: int


class CardIdWithValue(NamedTuple):
    """The value of a given count of a card.

    The value is for the count-th copy of a card."""
    card_id: CardId
    count: int
    value: float


def str_to_snake(string: str):
    return string.replace(" ", "_")


def snake_to_str(snake):
    return snake.replace("_", " ")


class AllCards:
    def __init__(self):
        raw_cards = Card.query.all()
        self._dict = self._init_dict(raw_cards)
        self._autocompleter = self._init_autocompleter(raw_cards)
        pass

    @staticmethod
    def _init_dict(raw_cards: typing.List[Card]) -> typing.Dict:
        card_dict = {CardId(set_num=card.set_num, card_num=card.card_num): card for card in raw_cards}
        return card_dict

    @staticmethod
    def _init_autocompleter(raw_cards: typing.List[Card]) -> DictStorageAutoCompleter:
        autocompleter = DictStorageAutoCompleter({})

        card_names = [str_to_snake(card.name) for card in raw_cards]
        autocompleter.train_from_strings(card_names)
        return autocompleter

    def __getitem__(self, item):
        return self._dict[item]

    def get_matching_card(self, search_str: str):
        guessed_phrases = self._autocompleter.guess_full_strings([search_str.replace(" ", "")])
        if guessed_phrases:
            return snake_to_str(guessed_phrases[0])
        else:
            return ''


ALL_CARDS = AllCards()


@dataclass
class CardDisplay:
    """Use make_card_display to use cached creation"""
    set_num: int
    card_num: int
    name: str
    rarity: models.rarity.Rarity
    image_url: str
    details_url: str

    @classmethod
    def from_card_id(cls, card_id: CardId):
        """Makes a CardDisplay from a CardId."""
        card = ALL_CARDS[card_id.set_num, card_id.card_num]
        return cls(set_num=card.set_num, card_num=card.card_num, name=card.name, rarity=card.rarity,
                   image_url=card.image_url, details_url=card.details_url)

    def to_dict(self):
        return self.__dict__
