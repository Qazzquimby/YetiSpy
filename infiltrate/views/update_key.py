import flask
import flask_login
from flask_classful import FlaskView

import infiltrate
import infiltrate.views.login
from infiltrate.models.user import get_by_id


# noinspection PyMethodMayBeStatic
class UpdateKeyView(FlaskView):
    """View for replacing a user's EW api key."""

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
