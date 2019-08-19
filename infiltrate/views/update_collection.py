"""This is where the routes are defined."""
from __future__ import annotations

import flask
import requests
from flask_classy import FlaskView

import models.deck_search
import models.user


# noinspection PyMethodMayBeStatic
class UpdateCollectionView(FlaskView):
    """View in which a user may update their collection."""

    def index(self):
        return flask.render_template('update_collection.html')

    def post(self):
        user = models.user.get_by_cookie()

        try:
            card_import = flask.request.form["import-cards-text"]
            # Import
            url = f"https://api.eternalwarcry.com/v1/useraccounts/updatecollection"
            data = {"key": user.key,
                    "cards": card_import}
            requests.post(url=url, data=data)
        except KeyError:
            pass
        user.update_collection()
        return ""
