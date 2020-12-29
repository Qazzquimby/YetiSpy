import flask
import flask_login
from flask_classful import FlaskView

from infiltrate.views.card_values.card_displays import CardDisplays


# noinspection PyMethodMayBeStatic
class RawDataView(FlaskView):
    """View to supply raw data files."""

    def card_evaluation(self):
        card_displays = CardDisplays.make_for_user(flask_login.current_user)
        value_frame = card_displays.value_info
        csv = value_frame.to_csv()

        response = flask.make_response(csv, 200)
        response.mimetype = "text/plain"
        return response
