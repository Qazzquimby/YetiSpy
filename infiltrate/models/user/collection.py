"""The cards a user owns"""

import typing as t

import sqlalchemy.exc

import browser
import caches
import card_collections
import models.card
import models.user.owns_card
from infiltrate import db

if t.TYPE_CHECKING:
    from models.user import User


def update_collection(user: "User"):
    updater = _CollectionUpdater(user)
    updater.run()


class _CollectionUpdater:
    """Runner class to update user's collection to match their
    Eternal Warcry collection."""

    def __init__(self, user: "User"):
        self.user = user

    def run(self):
        """Updates the given user's collection to match their Eternal Warcry
        collection."""
        self._remove_old_collection()
        collection = self._get_new_collection()
        self._add_new_collection(collection)

    def _get_new_collection(self) -> t.Dict[models.card.CardId, int]:
        url = (
            f"https://api.eternalwarcry.com/v1/useraccounts/collection"
            f"?key={self.user.key}"
        )
        response = browser.obj_from_url(url)
        cards = response["cards"]
        collection = card_collections.make_collection_from_ew_export(cards)
        # TODO IMPORTANT This needs to invalidate the caches for card values
        #  and user_ownership_cache.
        return collection

    def _remove_old_collection(self):
        (
            models.user.owns_card.UserOwnsCard.query.filter_by(
                user_id=self.user.id
            ).delete()
        )

    def _add_new_collection(self, collection: t.Dict, retry=True):
        try:
            for card_id in collection.keys():
                user_owns_card = models.user.owns_card.UserOwnsCard(
                    user_id=self.user.id,
                    set_num=card_id.set_num,
                    card_num=card_id.card_num,
                    count=collection[card_id],
                )
                self.user.cards.append(user_owns_card)
                db.session.add(user_owns_card)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            if retry:
                db.session.rollback()

                # Missing cards used by Eternal Warcry can cause this error.
                models.card.update_cards()
                self._add_new_collection(collection, retry=False)
            else:
                raise e


class UserOwnershipCache:
    """Cache for cards owned by each user."""

    def __init__(self, user: "User"):
        self._dict = self._init_dict(user)

    @staticmethod
    def _init_dict(user):
        raw_ownership = models.user.owns_card.UserOwnsCard.query.filter_by(
            user_id=user.id
        ).all()
        own_dict = {
            models.card.CardId(set_num=own.set_num, card_num=own.card_num): own
            for own in raw_ownership
        }
        return own_dict

    def __getitem__(self, item):
        return self._dict[item]


@caches.mem_cache.cache("ownership", expires=5 * 60)
def get_ownership_cache(user: "User"):
    return UserOwnershipCache(user)


def user_has_count_of_card(
    user: "User", card_id: models.card.CardId, count: int = 1
) -> bool:
    """Return if a user has at least count cards."""
    cache = get_ownership_cache(user)

    try:
        match = cache[card_id]
        owned_count = match.count
    except KeyError:
        owned_count = 0

    return count <= owned_count
