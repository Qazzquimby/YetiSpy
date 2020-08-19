import flask
import flask_login
from flask_classy import FlaskView

import models.card
import models.card.completion
import views.card_values.card_displays as card_displays
import views.card_values.display_filters as display_filters
import global_data


class CardsView(FlaskView):
    """View for the list of card values"""

    route_base = "/"

    def index(self):
        """The main card values page"""
        return flask.render_template("card_values/main.html")

    def card_values(self, page_num=0, sort_str="efficiency", owner_str=None):
        """A table loaded into the card values page."""

        page_num = int(page_num)
        sort = display_filters.get_sort(sort_str)
        if not owner_str:
            ownership = sort.default_ownership
        else:
            ownership = display_filters.get_owner(owner_str)

        all_cards = global_data.all_cards
        displays = card_displays.CardDisplays.make_for_user(
            flask_login.current_user, all_cards
        )

        displays = displays.configure(sort, ownership)

        cards_on_page = displays.get_page(page_num)

        return flask.render_template(
            "card_values/table.html",
            page=page_num,
            sort=sort_str,
            card_values=cards_on_page,
        )

    def card_search(self, search_str="_"):
        """Searches for cards with names matching the search string,
        by the method used in AllCards"""

        displays = card_displays.CardDisplays.make_for_user(
            flask_login.current_user, global_data.all_cards
        )

        search_str = search_str[1:]
        search_str = search_str.lower()
        matching_card_df = models.card.completion.get_matching_card(
            displays.value_info, search_str
        )
        if len(matching_card_df) > 0:
            displays = card_displays.CardDisplayPage.format_ungrouped_page(
                matching_card_df
            )
            return flask.render_template("card_values/table.html", card_values=displays)
        else:
            return ""
