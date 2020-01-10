import flask
from flask_classy import FlaskView

import models.card
import profiling
import views.card_values.card_displays
import views.card_values.display_filters
import views.globals
import views.login
# from views.card_values import get_sort, get_owner, make_card_displays, CardDisplayPage
from views.login import AuthenticationException


class CardsView(FlaskView):
    """View for the list of card values"""
    route_base = '/'

    def index(self):
        """The main card values page"""
        try:
            user = views.login.get_by_cookie()
        except AuthenticationException:
            user = None

        if not user:
            return flask.redirect("/login")

        return flask.render_template("card_values.html")

    def card_values(self, page_num=1, sort_str="craft", owner_str=None):
        """A table loaded into the card values page."""
        try:
            user = views.login.get_by_cookie()
        except AuthenticationException:
            return flask.abort(401)

        page_num = int(page_num)
        sort = views.card_values.display_filters.get_sort(sort_str)
        if not owner_str:
            ownership = sort.default_ownership
        else:
            ownership = views.card_values.display_filters.get_owner(owner_str)

        profiling.start_timer("make_card_displays")
        all_cards = views.globals.all_cards
        displays = views.card_values.card_displays.make_card_displays(user, all_cards)
        profiling.end_timer("make_card_displays")

        displays = displays.configure(sort, ownership)

        cards_on_page = displays.get_page(page_num)

        return flask.render_template('card_values_table.html', page=page_num, sort=sort_str, card_values=cards_on_page)

    def card_search(self, search_str='_'):
        """Searches for cards with names matching the search string, by the method used in AllCards"""
        try:
            user = views.login.get_by_cookie()
        except AuthenticationException:
            return flask.redirect("/login")
        displays = views.card_values.card_displays.make_card_displays(user)

        search_str = search_str[1:]
        search_str = search_str.lower()
        matching_card_df = models.card.get_matching_card(displays.value_info, search_str)
        if len(matching_card_df) > 0:
            cards_in_search = matching_card_df
            displays = views.card_values.card_displays.CardDisplayPage.format_ungrouped_page(cards_in_search)
            return flask.render_template('card_values_table.html', card_values=displays)
        else:
            return ''
