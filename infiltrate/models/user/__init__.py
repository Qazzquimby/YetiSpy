"""User account objects"""
from __future__ import annotations

import typing

import flask
import sqlalchemy_utils
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine

import card_display
import cookies
import evaluation
import models.deck_search
from infiltrate import app, db
from models.user.collection import CollectionUpdater, UserOwnershipCache
from views.login import AuthenticationException


class User(db.Model):
    """Model representing a user."""
    __tablename__ = "users"
    id = db.Column("id", db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column("name", db.String(length=40))
    weighted_deck_searches: typing.List[models.deck_search.WeightedDeckSearch] = db.relationship("WeightedDeckSearch",
                                                                                                 cascade_backrefs=False)
    key = db.Column('key', sqlalchemy_utils.EncryptedType(db.String(50),
                                                          app.config["SECRET_KEY"],
                                                          FernetEngine))

    cards = db.relationship("UserOwnsCard")

    def update_collection(self):
        """Replaces a user's old collection in the db with their new collection."""
        CollectionUpdater(self)()

    def get_displays(self) -> typing.List[card_display.CardValueDisplay]:
        values = self.get_values()
        displays = [card_display.CardValueDisplay.from_card_id_with_value(v) for v in values]
        return displays

    def get_values(self) -> typing.List[cards.CardIdWithValue]:
        value_dict = evaluation.GetOverallValueDict(self.weighted_deck_searches)()
        values = list(value_dict)
        return values

    def add_weighted_deck_searches(self, searches: typing.List[models.deck_search.WeightedDeckSearch]):
        """Adds a weighted deck search to the user's table"""
        for search in searches:
            self.weighted_deck_searches.append(search)
            db.session.add(search)
        self._normalize_deck_search_weights()
        db.session.commit()

    def _normalize_deck_search_weights(self):
        """Ensures that a user's saved weights are approximately normalized to 1.
        This prevents weight sizes from inflating values."""
        total_weight = sum([search.weight for search in self.weighted_deck_searches])
        if not 0.9 < total_weight < 1.10:  # Bounds prevent repeated work due to rounding on later passes
            for search in self.weighted_deck_searches:
                search.weight = search.weight / total_weight


def get_by_cookie() -> typing.Optional[User]:
    user_id = flask.request.cookies.get(cookies.ID)
    if not user_id:
        return None
    user = get_by_id(user_id)
    if user:
        return user
    else:
        raise AuthenticationException  # User in cookie is not found in db


def get_by_id(user_id: str):
    user = User.query.filter_by(id=user_id).first()
    return user
