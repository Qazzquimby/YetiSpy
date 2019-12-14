"""The Card model and related utilities

Related to card_collections.py
"""
import json
import typing
from typing import NamedTuple

import pandas as pd
import sqlalchemy.exc
import sqlalchemy.orm
import sqlalchemy.orm.exc
from dataclasses import dataclass
from fast_autocomplete import AutoComplete

import browser
import df_types
import models.rarity
from infiltrate import db


class Card(db.Model):
    """Model representing an Eternal card."""
    __tablename__ = "cards"
    set_num = db.Column("SetNumber", db.Integer, primary_key=True)
    card_num = db.Column("EternalID", db.Integer, primary_key=True)
    name = db.Column("Name", db.String(length=40), unique=True, nullable=False)
    rarity = db.Column("Rarity", db.String(length=9), db.ForeignKey("rarities.Name"), nullable=False)
    image_url = db.Column("ImageUrl", db.String(length=100), unique=True, nullable=False)
    details_url = db.Column("DetailsUrl", db.String(length=100), unique=True, nullable=False)

    @property
    def id(self):
        """Returns the CardId for the Card."""
        try:
            card_id = CardId(set_num=self.set_num, card_num=self.card_num)
        except sqlalchemy.orm.exc.DetachedInstanceError as e:
            print("Detached Instance Error!", self, self.__dict__)
            raise e
        return card_id


Card_DF = df_types.make_dataframe_type(
    df_types.get_columns_for_model(Card)
)


def _get_card_json():
    card_json_str = browser.get_str_from_url_and_xpath("https://eternalwarcry.com/content/cards/eternal-cards.json",
                                                       "/html/body/pre")
    card_json = json.loads(card_json_str)

    return card_json


def _make_cards_from_entries(entries: typing.List[dict]):
    seen_ids = set()
    for entry in entries:
        if 'EternalID' in entry.keys():
            card_id = models.card.CardId(set_num=entry['SetNumber'], card_num=entry['EternalID'])
            if card_id not in seen_ids:
                _make_card_from_entry(entry)
                seen_ids.add(card_id)


def _make_card_from_entry(entry: dict) -> typing.Optional[Card]:
    if not entry["DeckBuildable"] or entry["Rarity"] == 'None':
        return
    card = Card(set_num=entry["SetNumber"],
                card_num=entry["EternalID"],
                name=entry["Name"],
                rarity=entry["Rarity"],
                image_url=entry["ImageUrl"],
                details_url=entry["DetailsUrl"])
    try:
        db.session.merge(card)
    except sqlalchemy.exc.IntegrityError:
        pass
    #     db.session.rollback()


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
    """Replaces spaces with _s in string."""
    return string.replace(" ", "_")


def snake_to_str(snake):
    """Replaces _s with spaces in string."""
    return snake.replace("_", " ")


class _CardAutoCompleter:
    def __init__(self, cards_df: Card_DF):
        self.cards = cards_df
        self.completer = self._init_autocompleter(cards_df)

    def get_cards_matching_search(self, search: str) -> Card_DF:
        """Returns cards with the name best matching the search string."""
        name = self._match_name(search)
        cards = self.cards[self.cards['name'].str.lower() == name]
        return cards

    def _match_name(self, search: str) -> typing.Optional[str]:
        """Return the closest matching card name to the search string"""
        try:
            result = self.completer.search(word=search, max_cost=3, size=1)[0][0]
            return result
        except IndexError:
            return None

    def _init_autocompleter(self, df: Card_DF):
        words = self._get_words(df)
        words = {word: {} for word in words}
        completer = AutoComplete(words=words)
        return completer

    @staticmethod
    def _get_words(df: Card_DF):
        names = df['name']
        return names


class _AllCardAutoCompleter(_CardAutoCompleter):
    """Handles autocompleting searches to card names from ALL_CARDS"""
    # TODO make this update when the card database updates
    # TODO totally untested
    completer: AutoComplete = None

    def __init__(self):
        if self.completer is None:
            super().__init__(ALL_CARDS)


def get_matching_card(card_df: Card_DF, search_str: str) -> Card_DF:
    """Return rows from the card_df with card names best matching the search_str."""
    matcher = _CardAutoCompleter(card_df)
    match = matcher.get_cards_matching_search(search_str)
    return match


class _AllCardsDataframe:
    def __init__(self):
        session = db.engine.raw_connection()  # sqlalchemy.orm.Session(db)
        cards_df = pd.read_sql_query("SELECT * from cards", session)
        cards_df.rename(columns={'SetNumber': 'set_num',
                                 'EternalID': 'card_num',
                                 'Name': 'name',
                                 'Rarity': 'rarity',
                                 'ImageUrl': 'image_url',
                                 "DetailsUrl": 'details_url'},
                        inplace=True)

        self.df = cards_df


def init_all_card_df():
    """Create a card dataframe for all cards in the database."""
    try:
        return _AllCardsDataframe().df
    except sqlalchemy.exc.ProgrammingError:
        print("CARDS TABLE NOT FOUND")


ALL_CARDS = init_all_card_df()


def card_exists(card_id: CardId):
    matching_card = models.card.ALL_CARDS.loc[
        (models.card.ALL_CARDS['set_num'] == card_id.set_num) & (models.card.ALL_CARDS['card_num'] == card_id.card_num)
        ]
    return len(matching_card) > 0


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
