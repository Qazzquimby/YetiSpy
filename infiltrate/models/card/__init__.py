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

import browser
import df_types
import models.rarity
from infiltrate import db


class CardId(NamedTuple):
    """A key to identify a card."""

    set_num: int
    card_num: int


class Card(db.Model):
    """Model representing an Eternal card."""

    __tablename__ = "cards"
    set_num = db.Column("SetNumber", db.Integer, primary_key=True)
    card_num = db.Column("EternalID", db.Integer, primary_key=True)
    name = db.Column("Name", db.String(length=40), unique=True, nullable=False)
    rarity = db.Column(
        "Rarity", db.String(length=9), db.ForeignKey("rarities.Name"), nullable=False
    )
    image_url = db.Column(
        "ImageUrl", db.String(length=100), unique=True, nullable=False
    )
    details_url = db.Column(
        "DetailsUrl", db.String(length=100), unique=True, nullable=False
    )
    is_in_draft_pack = db.Column("IsInDraftPack", db.Boolean, nullable=False)

    @property
    def id(self):
        """Returns the CardId for the Card."""
        try:
            card_id = CardId(set_num=self.set_num, card_num=self.card_num)
        except sqlalchemy.orm.exc.DetachedInstanceError as e:
            print("Detached Instance Error!", self, self.__dict__)
            raise e
        return card_id


Card_DF = df_types.make_dataframe_type(df_types.get_columns_for_model(Card))


class AllCards:
    """A global storage for all cards in the database."""

    def __init__(self):
        session = db.engine.raw_connection()
        cards_df = pd.read_sql_query("SELECT * from cards", session)
        cards_df.rename(
            columns={
                "SetNumber": "set_num",
                "EternalID": "card_num",
                "Name": "name",
                "Rarity": "rarity",
                "ImageUrl": "image_url",
                "DetailsUrl": "details_url",
                "IsInDraftPack": "is_in_draft_pack",
            },
            inplace=True,
        )

        self.df = cards_df

    def get_card(self, card_id: CardId):
        """Return the row matching the card id."""
        card = self.df[card_id.set_num, card_id.card_num]
        return card

    def card_exists(self, card_id: CardId):
        """Return if the card_id is found in the AllCards."""
        matching_card = self.df.loc[
            (
                (self.df["set_num"] == card_id.set_num)
                & (self.df["card_num"] == card_id.card_num)
            )
        ]
        does_exist = len(matching_card) > 0
        return does_exist


def update_cards():
    """Updates the db to match the Warcry cards list."""
    card_json = _get_card_json()
    _make_cards_from_entries(card_json)
    db.session.commit()


def _get_card_json():
    card_json_str = browser.get_str_from_url_and_xpath(
        "https://eternalwarcry.com/content/cards/eternal-cards.json", "/html/body/pre"
    )
    card_json = json.loads(card_json_str)

    return card_json


def _make_cards_from_entries(entries: typing.List[dict]):
    seen_ids = set()
    for entry in entries:
        if "EternalID" in entry.keys():
            card_id = models.card.CardId(
                set_num=entry["SetNumber"], card_num=entry["EternalID"]
            )
            if card_id not in seen_ids:
                _make_card_from_entry(entry)
                seen_ids.add(card_id)


def _make_card_from_entry(entry: dict) -> typing.Optional[Card]:
    if not entry["DeckBuildable"] or entry["Rarity"] == "None":
        return
    card = Card(
        set_num=entry["SetNumber"],
        card_num=entry["EternalID"],
        name=entry["Name"],
        rarity=entry["Rarity"],
        image_url=entry["ImageUrl"],
        details_url=entry["DetailsUrl"],
    )
    try:
        db.session.merge(card)
    except sqlalchemy.exc.IntegrityError:
        pass
    #     db.session.rollback()
