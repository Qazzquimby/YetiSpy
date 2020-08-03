import flask
import flask_classy

import card_evaluation
import global_data
import purchases
import views.login
from views.login import AuthenticationException


class PurchasesView(flask_classy.FlaskView):
    """View for the list of card values"""

    route_base = "/purchases"

    def index(self):
        """The main purchases page"""
        try:
            user = views.login.get_by_cookie()
        except AuthenticationException:
            user = None

        if not user:
            return flask.redirect("/login")

        return flask.render_template("purchase_values/main.html")

    def values(self, page_num=0, sort_str="efficiency", owner_str=None):
        """A table loaded into the card values page."""
        try:
            user = views.login.get_by_cookie()
        except AuthenticationException:
            return flask.abort(401)

        page_num = int(page_num)

        purchase_values = purchases.get_purchase_values(
            user=user,
            own_values=card_evaluation.OwnValueFrame.from_user(
                user=user, card_details=global_data.all_cards
            ),
        )

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
