"""User account objects"""

import typing as t

import sqlalchemy_utils
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine

import models.deck_search
import models.user.collection
from infiltrate import application, db


class User(db.Model):
    """Model representing a user."""

    __tablename__ = "users"
    id = db.Column("id", db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column("name", db.String(length=40))
    weighted_deck_searches: t.List[
        models.deck_search.WeightedDeckSearch
    ] = db.relationship("WeightedDeckSearch", cascade_backrefs=False)
    key = db.Column(
        "key",
        sqlalchemy_utils.EncryptedType(
            db.String(50), application.config["SECRET_KEY"], FernetEngine
        ),
    )

    def add_weighted_deck_searches(
        self, searches: t.List[models.deck_search.WeightedDeckSearch]
    ):
        """Adds a weighted deck search to the user's table"""
        for search in searches:
            self.weighted_deck_searches.append(search)
            db.session.add(search)
        self._normalize_deck_search_weights()
        db.session.commit()

    def _normalize_deck_search_weights(self):
        """Ensures that a user's saved weights are approximately normalized
        to 1.
        This prevents weight sizes from inflating values."""
        total_weight = sum([search.weight for search in self.weighted_deck_searches])
        # Bounds prevent repeated work due to rounding on later passes
        if not 0.9 < total_weight < 1.10:
            for search in self.weighted_deck_searches:
                search.weight = search.weight / total_weight


def get_by_id(user_id: int):
    user = User.query.filter_by(id=str(user_id)).first()
    return user
