import csv
import enum
import os
import typing
import urllib.error
from datetime import datetime

from progiter import ProgIter

from infiltrate import db, browser
from infiltrate.models.card import Card, card_in_db


class DeckHasCard(db.Model):
    deck_id = db.Column('deck_id', db.String(length=100), db.ForeignKey('decks.id'), primary_key=True)
    set_num = db.Column('set_num', db.Integer, primary_key=True)
    card_num = db.Column('card_num', db.Integer, primary_key=True)
    num_played = db.Column('num_played', db.Integer, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint([set_num, card_num], [Card.set_num, Card.card_num]), {})


class DeckType(enum.Enum):
    unknown = 0
    standard = 1
    draft = 2
    gauntlet = 3
    forge = 4
    campaign = 5
    event = 6


class Archetype(enum.Enum):
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
    cards = db.relationship('DeckHasCard')


def save_all_ids():
    def main():
        page = 0
        while True:
            ids_on_page = get_ids_from_page(page)
            if not ids_on_page:
                break
            save_ids(ids_on_page)
            page += 1
            print(f"{page * 50 * 100 / 19325}%")

    def get_ids_from_page(page: int):
        items_per_page = 50
        url = "https://api.eternalwarcry.com/v1/decks/SearchDecks" + \
              f"?starting={items_per_page * page}" + \
              f"&perpage={items_per_page}" + \
              f"&key=e6b3bf05-2fb7-4979-baf8-92328818e3f5"
        page_json = browser.get_content_at_url(url)
        ids = _get_ids_from_page_json(page_json)

        return ids

    def _get_ids_from_page_json(page_json: typing.Dict):
        decks = page_json['decks']
        ids = [deck['deck_id'] for deck in decks]
        return ids

    def save_ids(ids: typing.List[str]):
        with open(os.path.join('..', 'data', 'deck_ids.csv'), 'a+') as csv_file:
            for deck_id in ids:
                csv_file.write(f"{deck_id},")

    main()


def deck_in_db(deck_id: str):
    return Deck.query.filter_by(id=deck_id).first()


def update_all_decks():
    def update_deck_from_id(deck_id: str):
        url = "https://api.eternalwarcry.com/v1/decks/details" + \
              "?key=e6b3bf05-2fb7-4979-baf8-92328818e3f5" + \
              f"&deck_id={deck_id}"
        try:
            page_json = browser.get_content_at_url(url)
        except (ConnectionError, urllib.error.HTTPError):
            return

        make_deck_from_details_json(page_json)

    def add_cards_to_deck(deck: Deck, page_json: typing.Dict):
        cards_json = page_json["deck_cards"] + page_json["sideboard_cards"] + page_json["market_cards"]

        for card_json in cards_json:
            set_num = card_json["set_number"]
            card_num = card_json["eternal_id"]
            if card_in_db(set_num, card_num):
                deck_has_card = DeckHasCard(
                    deck_id=page_json["deck_id"],
                    set_num=set_num,
                    card_num=card_num,
                    num_played=card_json["count"]
                )
                deck.cards.append(deck_has_card)

    def make_deck_from_details_json(page_json: typing.Dict):

        archetype = Archetype[page_json["archetype"].lower().replace(" ", "_")]
        deck_type = DeckType[page_json["deck_type"].lower()]

        deck = Deck(
            id=page_json['deck_id'],
            archetype=archetype,
            date_added=datetime.strptime(page_json["date_added_full"][:19], '%Y-%m-%dT%H:%M:%S'),
            date_updated=datetime.strptime(page_json["date_updated_full"][:19], '%Y-%m-%dT%H:%M:%S'),
            deck_type=deck_type,
            description=page_json["description"].encode('ascii', errors='ignore'),
            patch=page_json["patch"],
            username=page_json["username"],
            views=page_json["views"],
            rating=page_json["rating"]
        )

        add_cards_to_deck(deck, page_json)
        db.session.merge(deck)
        db.session.commit()

    def generate_ids():
        with open(os.path.join('..', 'data', 'deck_ids.csv'), 'r') as csv_file:
            ids = list(csv.reader(csv_file))[0]
            for deck_id in ids:
                yield deck_id

    for deck_id in ProgIter(generate_ids(), total=19350):
        if not deck_in_db(deck_id):
            update_deck_from_id(deck_id)


if __name__ == '__main__':
    update_all_decks()

# def _add_deck_from_url(url: str):
#     deck = Deck(id="someFakeId")  # , cards=[Card(set_num=0, card_num=36,)]
#     db.session.merge(deck)
#     db.session.commit()
#
#     connection = db.engine.connect()
#
#     card_playsets = [
#         ["someFakeId", 0, 36, 4],
#         ["someFakeId", 0, 35, 2]
#     ]
#
#     for playset in card_playsets:
#         try:
#             add_card = deck_has_card.insert(values=playset)
#             connection.execute(add_card)
#         except IntegrityError:
#             add_card = deck_has_card.update(values=playset)
#             connection.execute(add_card)
#
#     db.session.commit()
#
#
#
#
