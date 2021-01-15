import typing as t

import flask
import flask_login
import numpy as np
from flask_classful import FlaskView

import infiltrate.models.card.completion as completion
import infiltrate.views.card_values.card_displays as card_displays
import infiltrate.views.card_values.display_filters as display_filters


class CardsView(FlaskView):
    """View for the list of card values"""

    route_base = "/"

    def index(self):
        """The main card values page"""
        return flask.render_template("card_values/main.html")

    def card_values(self):
        """A table loaded into the card values page."""

        page_num = int(flask.request.args.get("page_num"))

        displays = self._get_displays()

        page_num = int(page_num)
        page_num, cards_on_page = displays.get_page(page_num)

        scaled = (np.log2(cards_on_page["play_craft_efficiency"] * 100) * 15).clip(
            lower=0
        )
        cards_on_page["scaled_play_craft_efficiency"] = scaled

        return flask.render_template(
            "card_values/table.html",
            page=page_num,
            sort=self._get_sort_str(),
            card_values=cards_on_page,
            cards_per_page=card_displays.CardDisplays.CARDS_PER_PAGE,
        )

    def card_search(self):
        """Searches for cards with names matching the search string,
        by the method used in AllCards"""

        displays = self._get_displays()

        search_str = flask.request.args.get("search_str")
        search_str = search_str.lower()
        cards_on_page = completion.get_matching_card(displays.value_info, search_str)

        scaled = (np.log2(cards_on_page["play_craft_efficiency"] * 100) * 15).clip(
            lower=0
        )
        cards_on_page["scaled_play_craft_efficiency"] = scaled

        return flask.render_template(
            "card_values/table.html",
            page=0,
            sort=self._get_sort_str(),
            card_values=cards_on_page,
            cards_per_page=16,
        )

    def _get_displays(self):
        sort = self._get_sort()
        filters = self._get_filters()
        displays = self._get_displays_from_sort_and_filters(sort, filters)
        return displays

    def _get_sort_str(self):
        sort_str = flask.request.args.get("sort_str")
        if sort_str is None:
            sort_str = "craft"
        return sort_str

    def _get_sort(self):
        sort_str = self._get_sort_str()
        return display_filters.get_sort(sort_str)

    def _get_filters(self):
        filter_names_and_defaults = [
            (
                "owner_str",
                [display_filters.UNOWNED_FILTER],
                display_filters.get_ownership_filter,
            ),
            ("excluded_rarities", [], display_filters.get_rarity_filter),
            (
                "only_expedition",
                [],
                lambda x: display_filters.OnlyExpeditionFilter()
                if x == "true"
                else None,
            ),
        ]
        filters = []
        for filter_name, default, getter in filter_names_and_defaults:
            filters_str = flask.request.args.get(filter_name)
            if filters_str is None:
                filter_strs = default
            else:
                filter_strs = [
                    _filter for _filter in filters_str.split(",") if len(_filter) > 0
                ]
            filters_for_type = [getter(filter_str) for filter_str in filter_strs]
            filters_for_type = [_filter for _filter in filters_for_type if _filter]
            filters += filters_for_type
        return filters

    def _get_displays_from_sort_and_filters(
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
