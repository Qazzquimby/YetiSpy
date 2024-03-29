"""The Deck model and related utilities"""
import enum
import logging
import typing as t
import urllib.error
from datetime import datetime

import tqdm

import infiltrate.browsers as browsers
import infiltrate.global_data as global_data
import infiltrate.models.card as card

# todo replace application with config injection
from infiltrate import application, db


class DeckHasCard(db.Model):
    """A table showing how many copies of a card a deck has."""

    deck_id = db.Column(
        "deck_id", db.String(length=100), db.ForeignKey("decks.id"), primary_key=True
    )
    set_num = db.Column("set_num", db.Integer, primary_key=True)
    card_num = db.Column("card_num", db.Integer, primary_key=True)
    num_played = db.Column("num_played", db.Integer, nullable=False)
    __table_args__ = (
        db.ForeignKeyConstraint(
            [set_num, card_num],
            [card.Card.set_num, card.Card.card_num],
            ondelete="CASCADE",
        ),
        {},
    )

    def to_card_id(self) -> card.CardId:
        return card.CardId(set_num=self.set_num, card_num=self.card_num)


class DeckType(enum.Enum):
    """Enum for deck types matching Warcry"""

    unknown = 0
    standard = 1
    throne = 1
    draft = 2
    gauntlet = 3
    forge = 4
    campaign = 5
    event = 6
    _ = 7
    expedition = 8
    other = 9


class Archetype(enum.Enum):
    """Enum for deck archetypes matching Warcry"""

    unknown = 0
    aggro = 1
    midrange = 2
    combo = 3
    control = 4
    tempo = 5
    aggro_control = 6
    aggro_combo = 7
    aggro_midrange = 8
    control_combo = 9
    control_midrange = 10
    tempo_combo = 11
    tempo_control = 12
    combo_midrange = 13


class Deck(db.Model):
    """Model representing an Eternal Deck from Warcry"""

    __tablename__ = "decks"
    id = db.Column("id", db.String(length=100), primary_key=True)
    archetype = db.Column("archetype", db.Enum(Archetype), nullable=True)
    date_added = db.Column("date_added", db.DateTime)
    date_updated = db.Column("date_updated", db.DateTime)
    deck_type = db.Column("deck_type", db.Enum(DeckType))
    description = db.Column("description", db.Text, nullable=True)
    patch = db.Column("patch", db.String(length=10))
    username = db.Column("username", db.String(length=30))
    views = db.Column("views", db.Integer)
    rating = db.Column("rating", db.Integer)
    cards = db.relationship("DeckHasCard")

    @classmethod
    def get_from_id(cls, deck_id: str):
        """Gets the deck matching the deck id."""
        return Deck.query.filter_by(id=deck_id).first()


# noinspection PyMissingOrEmptyDocstring
class _WarcryNewIdGetter:
    ITEMS_PER_PAGE = 50

    def get_new_ids(self, max_decks=None):
        if max_decks is not None:
            max_pages = max_decks / self.ITEMS_PER_PAGE
        else:
            max_pages = None

        logging.info("Getting new deck ids")
        new_ids = []
        page = 0
        while True:
            ids_on_page = self.get_ids_from_page(page)
            new_ids_on_page = self.remove_old_ids(ids_on_page)
            new_ids += new_ids_on_page
            if not new_ids_on_page or max_pages is not None and page >= max_pages:
                # todo this may need testing.
                break

            page += 1
            logging.info(f"Pages of deck ids ready: {page}")
        return new_ids

    def get_ids_from_page(self, page: int):
        # TODO could find what deck search they belong to here and only keep the needed ones
        url = (
            "https://api.eternalwarcry.com/v1/decks/SearchDecks"
            + f"?starting={self.ITEMS_PER_PAGE * page}"
            + f"&perpage={self.ITEMS_PER_PAGE}"
            + f"&key={application.config['WARCRY_KEY']}"
        )
        page_json = browsers.get_json_from_url(url)
        ids = self.get_ids_from_page_json(page_json)

        return ids

    @staticmethod
    def get_ids_from_page_json(page_json: t.Dict):
        decks = page_json["decks"]
        ids = [deck["deck_id"] for deck in decks]
        return ids

    @staticmethod
    def remove_old_ids(ids: t.List[str]) -> t.List[str]:
        new_ids = []
        for deck_id in ids:
            if not Deck.get_from_id(deck_id):
                new_ids.append(deck_id)
            else:
                break
        return new_ids


def get_new_warcry_ids(max_decks=1_000):
    """Return all Warcry deck IDs newer than any in the database."""

    id_getter = _WarcryNewIdGetter()
    ids = id_getter.get_new_ids(max_decks=max_decks)

    return ids


def update_decks():
    """Updates the database with all new Warcry decks"""

    # noinspection PyMissingOrEmptyDocstring
    class _WarcyDeckUpdater:
        def run(self):
            ids = get_new_warcry_ids(1_000)

            for deck_id in tqdm.tqdm(ids, desc="Updating decks"):
                self.update_deck(deck_id)

        def update_deck(self, deck_id: str):
            url = (
                "https://api.eternalwarcry.com/v1/decks/details"
                + f"?key={application.config['WARCRY_KEY']}"
                + f"&deck_id={deck_id}"
            )
            try:
                page_json = browsers.get_json_from_url(url)
            except (ConnectionError, urllib.error.HTTPError):
                return

            self.make_deck_from_details_json(page_json)

        def make_deck_from_details_json(self, page_json: t.Dict):

            archetype = Archetype[page_json["archetype"].lower().replace(" ", "_")]
            try:
                deck_type = DeckType.__dict__[
                    page_json["deck_type"].lower().replace(" ", "_")
                ]
            except KeyError:  # not sure this is the right exception
                deck_type = DeckType(int(page_json["deck_type"]))

            deck = Deck(
                id=page_json["deck_id"],
                archetype=archetype,
                date_added=datetime.strptime(
                    page_json["date_added_full"][:19], "%Y-%m-%dT%H:%M:%S"
                ),
                date_updated=datetime.strptime(
                    page_json["date_updated_full"][:19], "%Y-%m-%dT%H:%M:%S"
                ),
                deck_type=deck_type,
                description=page_json["description"].encode("ascii", errors="ignore"),
                patch=page_json["patch"],
                username=page_json["username"],
                views=page_json["views"],
                rating=page_json["rating"],
            )

            self.add_cards_to_deck(deck, page_json)
            db.session.merge(deck)
            db.session.commit()

        @staticmethod
        def add_cards_to_deck(deck: Deck, page_json: t.Dict):
            cards_json = (
                page_json["deck_cards"]
                + page_json["sideboard_cards"]
                + page_json["market_cards"]
            )

            for card_json in cards_json:
                set_num = card_json["set_number"]
                card_num = card_json["eternal_id"]
                card_id = card.CardId(set_num, card_num)

                # todo better to pass all_cards to this than use the global
                if global_data.all_cards.card_exists(card_id):
                    deck_has_card = DeckHasCard(
                        deck_id=page_json["deck_id"],
                        set_num=set_num,
                        card_num=card_num,
                        num_played=card_json["count"],
                    )
                    deck.cards.append(deck_has_card)

    logging.info("Updating decks")
    updater = _WarcyDeckUpdater()
    updater.run()
