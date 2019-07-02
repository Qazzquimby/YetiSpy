"""User account objects"""

import re
import typing

from infiltrate import card_collections
from infiltrate import models
from infiltrate.models import db


class UserOwnsCard(db.Model):
    """Table representing card playset ownership."""
    username = db.Column('username', db.String(length=20), db.ForeignKey('users.name'), primary_key=True)
    set_num = db.Column('set_num', db.Integer, primary_key=True)
    card_num = db.Column('card_num', db.Integer, primary_key=True)
    count = db.Column('count', db.Integer, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint((set_num, card_num), [models.card.Card.set_num,
                                                                    models.card.Card.card_num]), {})


class User(db.Model):
    """Model representing a user."""
    __tablename__ = "users"
    name = db.Column("name", db.String(length=20), primary_key=True)
    weighted_deck_searches = db.relationship("WeightedDeckSearch", cascade_backrefs=False)
    cards = db.relationship("UserOwnsCard")


def update_collection(user: User, collection: typing.Dict):
    """Replaces a user's old collection in the db with their new collection."""
    _remove_old_collection(user)
    _add_new_collection(user, collection)


def _remove_old_collection(user: User):
    UserOwnsCard.query.filter_by(username=user.name).delete()


def _add_new_collection(user: User, collection: typing.Dict):
    for card_id in collection.keys():
        user_owns_card = UserOwnsCard(
            username=user.name,
            set_num=card_id.set_num,
            card_num=card_id.card_num,
            count=collection[card_id]
        )
        user.cards.append(user_owns_card)
        db.session.add(user_owns_card)
    db.session.commit()


def _temp_get_collection_from_txt():
    # todo kill this. It won't be used in the web interface.
    def _from_export_text(text):
        numbers = [int(number) for number in re.findall(r'\d+', text)]
        if len(numbers) == 3:
            count = numbers[0]
            set_num = numbers[1]
            card_num = numbers[2]
            playset = card_collections.CardPlayset(
                card_collections.CardId(card_num=card_num, set_num=set_num), count=count)

            return playset
        return None

    with open("collection.txt") as collection_file:
        collection_text = collection_file.read()
        collection_lines = collection_text.split("\n")

        playsets = card_collections.make_card_playset_dict()
        for line in collection_lines:
            if "*Premium*" not in line:
                playset = _from_export_text(line)
                if playset:
                    playsets[playset.card_id] = playset.count
    return playsets
