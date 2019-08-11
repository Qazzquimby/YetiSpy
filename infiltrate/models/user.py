"""User account objects"""
import typing

import flask
import sqlalchemy_utils
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine

import browser
import caches
import card_collections
import cookies
import models.card
import models.deck_search
from infiltrate import app, db
from views.account_view import AuthenticationException


class UserOwnsCard(db.Model):
    """Table representing card playset ownership."""
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('users.id'), primary_key=True)
    set_num = db.Column('set_num', db.Integer, primary_key=True)
    card_num = db.Column('card_num', db.Integer, primary_key=True)
    count = db.Column('count', db.Integer, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint((set_num, card_num), [models.card.Card.set_num,
                                                                    models.card.Card.card_num]), {})


class User(db.Model):
    """Model representing a user."""
    __tablename__ = "users"
    id = db.Column("id", db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column("name", db.String(length=40))
    weighted_deck_searches: typing.List[models.deck_search.WeightedDeckSearch] = db.relationship("WeightedDeckSearch",
                                                                                                 cascade_backrefs=False)
    # key = db.Column('key', sqlalchemy_utils.PasswordType(schemes=['pbkdf2_sha512']))
    key = db.Column('key', sqlalchemy_utils.EncryptedType(db.String(50),
                                                          app.config["SECRET_KEY"],
                                                          FernetEngine))

    cards = db.relationship("UserOwnsCard")

    def update_collection(self):
        """Replaces a user's old collection in the db with their new collection."""
        updater = _CollectionUpdater(self)  # TODO split into smaller classes
        collection = self._get_new_collection()
        updater(collection)

    def _get_new_collection(self) -> typing.Dict[models.card.CardId, int]:
        url = f"https://api.eternalwarcry.com/v1/useraccounts/collection?key={self.key}"
        response = browser.obj_from_url(url)
        cards = response["cards"]
        collection = card_collections.make_collection_from_ew_export(cards)
        return collection

    def get_overall_value_dict(self) -> card_collections.ValueDict:
        """Gets a ValueDict for a user based on all their weighted deck searches."""
        values = card_collections.ValueDict()

        for card in models.card.ALL_CARDS:
            for play_count in range(4):
                values[card.id][play_count] += 0

        value_dicts = self._get_individual_value_dicts()
        for value_dict in value_dicts:
            for card_id in value_dict.keys():
                for play_count in range(4):
                    values[card_id][play_count] += value_dict[card_id][play_count]
        return values

    def _get_individual_value_dicts(self) -> typing.List[card_collections.ValueDict]:
        """Get a list of ValueDicts for a user, each based on a single weighted deck search."""
        value_dicts = []
        for weighted_search in self.weighted_deck_searches:
            value_dict = weighted_search.get_value_dict()

            value_dicts.append(value_dict)
        return value_dicts

    def add_weighted_deck_searches(self, searches: typing.List[models.deck_search.WeightedDeckSearch]):
        """Adds a weighted deck search to the user's table"""
        for search in searches:
            self._add_weighted_deck_search(search)
        self._normalize_deck_search_weights()
        db.session.commit()

    def _add_weighted_deck_search(self, search: models.deck_search.WeightedDeckSearch):
        self.weighted_deck_searches.append(search)
        db.session.add(search)

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


@caches.mem_cache.cache("ownership", expires=5 * 60)
def get_ownership_cache(user: User):
    return UserOwnershipCache(user)


class UserOwnershipCache:
    def __init__(self, user: User):
        self._dict = self._init_dict(user)

    @staticmethod
    def _init_dict(user):
        # TODO this is redundant with AllCards class
        raw_ownership = UserOwnsCard.query.filter_by(user_id=user.id).all()
        own_dict = {models.card.CardId(set_num=own.set_num, card_num=own.card_num): own
                    for own in raw_ownership}
        return own_dict

    def __getitem__(self, item):
        return self._dict[item]


def user_has_count_of_card(user: User, card_id: models.card.CardId, count: int = 1):
    cache = get_ownership_cache(user)

    try:
        match = cache[card_id]
        owned_count = match.count
    except KeyError:
        owned_count = 0

    return count <= owned_count


class _CollectionUpdater:
    def __init__(self, user: User):
        self.user = user

    def __call__(self, collection):
        self._remove_old_collection()
        self._add_new_collection(collection)

    def _remove_old_collection(self):
        UserOwnsCard.query.filter_by(user_id=self.user.id).delete()

    def _add_new_collection(self, collection: typing.Dict):
        for card_id in collection.keys():
            user_owns_card = UserOwnsCard(
                user_id=self.user.id,
                set_num=card_id.set_num,
                card_num=card_id.card_num,
                count=collection[card_id]
            )
            self.user.cards.append(user_owns_card)
            db.session.add(user_owns_card)
        db.session.commit()
