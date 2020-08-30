import flask
import flask_classy
import flask_login

import infiltrate.card_evaluation as card_evaluation
import infiltrate.global_data as global_data
import infiltrate.purchases as purchases


class PurchasesView(flask_classy.FlaskView):
    """View for the list of card values"""

    route_base = "/purchases"

    def index(self):
        """The main purchases page"""
        return flask.render_template("purchase_values/main.html")

    def values(self, page_num=0, sort_str="efficiency", owner_str=None):
        """A table loaded into the card values page."""
        page_num = int(page_num)

        purchase_values = purchases.get_purchase_values(
            user=flask_login.current_user,
            own_values=card_evaluation.OwnValueFrame.from_user(
                user=flask_login.current_user, card_details=global_data.all_cards
            ),
        )
        purchase_values = purchase_values.query("value > 0")

        if sort_str == "efficiency":
            displays = purchase_values.sort_values("value_per_gold", ascending=False)
        elif sort_str == "value":
            displays = purchase_values.sort_values("value", ascending=False)
        else:
            raise ValueError("sort string must be one of efficiency or value")

        return flask.render_template(
            "purchase_values/table.html",
            page=page_num,
            sort=sort_str,
            purchase_values=displays,
        )
