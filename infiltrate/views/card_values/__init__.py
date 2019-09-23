import flask
from flask_classy import FlaskView

import models.card
import models.user
import profiling
import views.login
from views.card_values.card_displays import make_card_displays
from views.card_values.display_filters import get_owner, get_sort
from views.login import AuthenticationException


# noinspection PyMethodMayBeStatic
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
        sort = get_sort(sort_str)
        if not owner_str:
            ownership = sort.default_ownership
        else:
            ownership = get_owner(owner_str)

        profiling.start_timer("make_card_displays")
        displays = make_card_displays(user)
        profiling.end_timer("make_card_displays")

        profiling.start_timer("configure")
        displays = displays.configure(sort, ownership)  # todo make fast
        profiling.end_timer("configure")

        cards_on_page = displays.get_page(page_num)

        return flask.render_template('card_values_table.html', page=page_num, sort=sort_str, card_values=cards_on_page)

    def card_search(self, search_str='_'):
        """Searches for cards with names matching the search string, by the method used in AllCards"""
        try:
            user = views.login.get_by_cookie()
        except AuthenticationException:
            return flask.redirect("/login")
        displays = make_card_displays(user)

        search_str = search_str[1:]
        matching_card = models.card.ALL_CARDS.get_matching_card(search_str)
        if matching_card:
            cards_on_page = displays.get_card(matching_card.id)
            return flask.render_template('card_values_table.html', card_values=cards_on_page)
        else:
            return ''
