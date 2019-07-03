"""The Card model and related utilities

Related to card_collections.py
"""
import json
import typing
from typing import NamedTuple

from infiltrate import browser
from infiltrate import caches
from infiltrate.models import db


@caches.mem_cache.cache("cards", expire="800")
def get_card(set_num: int, card_num: int):
    """Gets a card with given set_num and card_num"""
    card = Card.query.filter_by(set_num=set_num, card_num=card_num).first()
    return card


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


class CardDisplay:
    """Use make_card_display to use cached creation"""

    def __init__(self, card_id: CardId):
        card = get_card(card_id.set_num, card_id.card_num)
        self.set_num = card.set_num
        self.card_num = card.card_num
        self.name = card.name
        self.rarity = card.rarity
        self.image_url = card.image_url
        self.details_url = card.details_url
