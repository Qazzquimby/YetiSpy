"""The Card model and related utilities

Related to card_collections.py
"""
import logging
import typing as t

import pandas as pd
import sqlalchemy.exc
import sqlalchemy.orm
import sqlalchemy.orm.exc

import infiltrate.browsers as browsers
import infiltrate.df_types as df_types
import infiltrate.models.rarity as rarity
from infiltrate import db


class CardId(t.NamedTuple):
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
    is_in_expedition = db.Column("IsInExpedition", db.Boolean, nullable=False)

    @property
    def id(self):
        """Returns the CardId for the Card."""
        try:
            card_id = CardId(set_num=self.set_num, card_num=self.card_num)
        except sqlalchemy.orm.exc.DetachedInstanceError as e:
            logging.error("Detached Instance Error!", self, self.__dict__)
            raise e
        return card_id


Card_DF = df_types.make_dataframe_type(df_types.get_columns_for_model(Card))


def all_cards_df_from_db() -> pd.DataFrame:
    """Return all rows from the cards table."""
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
            "IsInExpedition": "is_in_expedition",
        },
        inplace=True,
    )

    cards_df["rarity"] = cards_df.rarity.apply(
        lambda rarity_name: rarity.rarity_from_name[rarity_name]
    )

    return cards_df


def get_card_ids_from_names(names: t.List[str]) -> t.List[CardId]:
    from infiltrate.global_data import all_cards

    matching_cards = all_cards[all_cards["name"].isin(names)]
    card_ids = [
        CardId(set_num=card_row["set_num"], card_num=card_row["card_num"])
        for card_row in matching_cards
    ]
    return card_ids


def update_cards():
    """Updates the db to match the Warcry cards list."""
    logging.info("Updating cards")
    card_json = _get_card_json()
    _make_cards_from_entries(card_json)
    db.session.commit()
    import infiltrate.models.card.draft as draft

    draft.update_is_in_draft_pack()

    import infiltrate.models.card.expedition as expedition

    expedition.update_is_in_expedition()


def _get_card_json():
    card_json = browsers.get_json_from_url(
        "https://eternalwarcry.com/content/cards/eternal-cards.json"
    )

    return card_json


def _make_cards_from_entries(entries: t.List[dict]):
    seen_ids = set()
    for entry in entries:
        if "EternalID" in entry.keys():
            card_id = CardId(set_num=entry["SetNumber"], card_num=entry["EternalID"])
            if card_id not in seen_ids:
                _make_card_from_entry(entry)
                seen_ids.add(card_id)


def _make_card_from_entry(entry: dict) -> t.Optional[Card]:
    if not entry["DeckBuildable"] or entry["Rarity"] == "None":
        return
    card = Card(
        set_num=entry["SetNumber"],
        card_num=entry["EternalID"],
        name=entry["Name"],
        rarity=entry["Rarity"],
        image_url=entry["ImageUrl"],
        details_url=entry["DetailsUrl"],
        is_in_draft_pack=False,  # Default value
        is_in_expedition=False,  # Default value
    )
    try:
        db.session.merge(card)
    except sqlalchemy.exc.IntegrityError:
        pass
    #     db.session.rollback()


if __name__ == "__main__":
    update_cards()
