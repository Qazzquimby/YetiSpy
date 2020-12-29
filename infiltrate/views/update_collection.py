"""This is where the routes are defined."""
import flask
import requests
from flask_classful import FlaskView
import flask_login

# noinspection PyMethodMayBeStatic
import infiltrate.models.user


class UpdateCollectionView(FlaskView):
    """View in which a user may update their collection."""

    def index(self):
        return flask.render_template("update_collection.html")

    def post(self):
        user = flask_login.current_user
        user_model = infiltrate.models.user.get_by_id(user.id)
        try:
            card_import = flask.request.form["import-cards-text"]
            # Import
            url = f"https://api.eternalwarcry.com/v1/useraccounts/updatecollection"
            data = {"key": user_model.ew_key, "cards": card_import}
            requests.post(url=url, data=data)
        except KeyError:
            pass
        return ""
