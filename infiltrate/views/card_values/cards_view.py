import typing as t

import flask
import flask_login
import numpy as np
from flask_classful import FlaskView

import infiltrate.models.card.completion as completion
import infiltrate.models.rarity
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
        try:
            sort = display_filters.get_sort(sort_str)
        except KeyError:
            sort = display_filters.CraftSort

        filter_names_and_defaults = [
            ("owner_str", display_filters.UNOWNED_FILTER),
            # ("rarities", list(infiltrate.models.rarity.rarity_from_name.keys()))
        ]
        filters = []
        for filter_name, default in filter_names_and_defaults:
            filter_str = flask.request.args.get(filter_name)
            try:
                _filter = display_filters.get_filter(
                    filter_str
                )  # TODO REWORK GET OWNER
            except KeyError:
                _filter = default
            filters.append(_filter)

        displays = self._get_displays(sort, filters)

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

    def card_search(
        self,
        search_str="_",
        sort_str=display_filters.EFFICIENCY_SORT,
        filters: t.List[display_filters.Filter] = None,
    ):
        """Searches for cards with names matching the search string,
        by the method used in AllCards"""
        if filters is None:
            filters = []

        displays = self._get_displays(sort_str, filters)

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

    def _get_displays(
        self,
        sort: display_filters.CardDisplaySort = display_filters.CraftSort,
        filters: t.List[display_filters.Filter] = None,
    ):
        if filters is None:
            filters = []

        displays = card_displays.CardDisplays.make_for_user(flask_login.current_user)

        for _filter in filters:
            displays.filter(_filter)
        displays.sort_method = sort

        displays.value_info["rank"] = np.arange(1, len(displays.value_info) + 1)
        return displays
