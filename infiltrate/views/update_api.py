"""Private API to trigger database updates while site is live."""

from flask_classy import FlaskView

import caches
import models.card
import models.deck
import models.deck_search
from infiltrate import application

NO_KEY_GIVEN = "no_key_given"


# TODO INVALIDATE ALL CACHES. Otherwise they're out of date.
# Local run api is http://127.0.0.1:5000/secret_update/update_all/KEY


# noinspection PyMethodMayBeStatic
class UpdateAPI(FlaskView):
    """View for the list of card values"""

    route_base = "/secret_update"
    key = application.config["UPDATE_KEY"]

    def refuse_bad_key(self, key):
        if key != self.key:
            return "Bad Key"

    def update_all(self, key=NO_KEY_GIVEN):
        self.refuse_bad_key(key)
        self.update_cards(key)
        self.update_decks(key)
        self.update_deck_searches(key)
        return "Updated All"

    def update_cards(self, key=NO_KEY_GIVEN):
        self.refuse_bad_key(key)
        models.card.update_cards()
        caches.invalidate()
        return "Updated Cards"

    def update_decks(self, key=NO_KEY_GIVEN):
        self.refuse_bad_key(key)
        models.deck.update_decks()
        caches.invalidate()
        return "Updated Decks"

    def update_deck_searches(self, key=NO_KEY_GIVEN):
        self.refuse_bad_key(key)
        models.deck_search.update_deck_searches()
        caches.invalidate()
        return "Updated Deck Searches"
