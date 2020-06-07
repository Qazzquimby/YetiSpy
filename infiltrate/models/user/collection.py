"""The cards a user owns"""

import typing as t

import sqlalchemy.exc

import browser
import card_collections
import models.card
import models.user.owns_card
from infiltrate import db

if t.TYPE_CHECKING:
    from models.user import User


def update_collection(user: "User"):
    """Update the user's collection to match their Eternal Warcry collection."""
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
        db.session.commit()

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

                # Missing cards used by Eternal Warcry can cause this error, so add
                #   missing cards.
                models.card.update_cards()
                self._remove_old_collection()
                self._add_new_collection(collection, retry=False)
            else:
                raise e
