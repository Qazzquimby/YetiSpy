import flask
import flask_login
import numpy as np
from flask_classy import FlaskView

import infiltrate.models.card.completion as completion
import infiltrate.views.card_values.card_displays as card_displays
import infiltrate.views.card_values.display_filters as display_filters


class CardsView(FlaskView):
    """View for the list of card values"""

    route_base = "/"

    def index(self):
        """The main card values page"""
        return flask.render_template("card_values/main.html")

    def card_values(self, page_num=0):
        """A table loaded into the card values page."""

        sort_str = flask.request.args.get("sort_str")
        owner_str = flask.request.args.get("owner_str")

        displays = self._get_displays(sort_str, owner_str)

        page_num = int(page_num)
        page_num, cards_on_page = displays.get_page(page_num)

        scaled = (np.log2(cards_on_page["play_craft_efficiency"] * 100) * 15).clip(
            lower=0
        )
        cards_on_page["scaled_play_craft_efficiency"] = scaled

        return flask.render_template(
            "card_values/table.html",
            page=page_num,
            sort=sort_str,
            card_values=cards_on_page,
            cards_per_page=card_displays.CardDisplays.CARDS_PER_PAGE,
        )

    def card_search(self, search_str="_", sort_str="efficiency", owner_str=None):
        """Searches for cards with names matching the search string,
        by the method used in AllCards"""

        displays = self._get_displays(sort_str, owner_str)

        search_str = search_str[1:]
        search_str = search_str.lower()
        cards_on_page = completion.get_matching_card(displays.value_info, search_str)

        scaled = (np.log2(cards_on_page["play_craft_efficiency"] * 100) * 15).clip(
            lower=0
        )
        cards_on_page["scaled_play_craft_efficiency"] = scaled

        return flask.render_template(
            "card_values/table.html",
            page=0,
            sort=sort_str,
            card_values=cards_on_page,
            cards_per_page=16,
        )

    def _get_displays(self, sort_str="efficiency", owner_str=None):
        sort = display_filters.get_sort(sort_str)
        if not owner_str:
            ownership = sort.default_ownership
        else:
            ownership = display_filters.get_owner(owner_str)

        displays = card_displays.CardDisplays.make_for_user(flask_login.current_user)
        displays = displays.configure(sort, ownership)
        displays.value_info["rank"] = np.arange(1, len(displays.value_info) + 1)
        return displays
