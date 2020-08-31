"""This is where the routes are defined."""
import flask

import infiltrate
import infiltrate.views.login
from infiltrate.models.user import User, get_by_id
from flask_classy import FlaskView
import flask_login


# noinspection PyMethodMayBeStatic
class UpdateKeyView(FlaskView):
    """View in which a user may update their collection."""

    @flask_login.login_required
    def post(self):
        try:
            new_key = flask.request.form["new-key"]
        except KeyError:
            raise ValueError("No key given.")

        if not infiltrate.views.login.ew_key_is_authentic(new_key):
            raise ValueError("Bad EW key.")

        user = flask_login.current_user
        user_model = get_by_id(user.id)
        user_model.ew_key = new_key
        infiltrate.db.session.commit()

        return ""
