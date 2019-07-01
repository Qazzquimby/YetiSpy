"""This is where the routes are defined."""
import typing

import flask
from flask_classy import FlaskView

from infiltrate import evaluation
from infiltrate.evaluation import CardValueDisplay
from infiltrate.models import user as user_mod


def group_card_value_displays(displays):
    def get_minimum_count(card):
        return min([c.count for c in displays if c.name == card.name])

    def get_maximum_count(card):
        return max([c.count for c in displays if c.name == card.name])

    def remove_duplicates(displays):
        names = [c.name for c in displays]
        first_indexes = set([names.index(name) for name in names])

        new_displays = []
        for i, card in enumerate(displays):
            if i in first_indexes:
                new_displays.append(card)
        return new_displays

    minimum_counts = {}
    maximum_counts = {}
    for card in displays:
        if card.name not in maximum_counts.keys():
            minimum_counts[card.name] = get_minimum_count(card)
            maximum_counts[card.name] = get_maximum_count(card)

    displays = remove_duplicates(displays)
    for card in displays:
        card.minimum = minimum_counts[card.name]
        card.maximum = maximum_counts[card.name]

    return displays


def sort_values(values: typing.List, sort: str):
    if sort == "value":
        key = lambda x: x.value
    elif sort == "craft":
        key = "value_per_shiftstone"  # TODO this is unfinished and broken

    return sorted(values, key=key, reverse=True)


def get_start_and_end_from_page(num_cards, page):
    cards_per_page = 30
    num_pages = int(num_cards / cards_per_page)
    if page < 0:
        page = num_pages + page + 1
    start = page * cards_per_page
    end = (page + 1) * cards_per_page
    return start, end


class CardsView(FlaskView):
    route_base = '/'

    def index(self):
        # TODO Read table from ajax
        # TODO allow searching through multiple pages of items.
        # TODO filter out cards by set (especially campaigns)
        # TODO update deck search cache on a schedule, nightly.
        # TODO add loading card images https://eternalwarcry.com/images/cards/loading.png
        # TODO divide values by something proportional to #decks in search (prevent larger searches being worth more)
        # TODO show number to buy with icons. Filled card for owned, Gold card for buy, Empty for dont

        return flask.render_template("card_values.html")

    def card_values(self, page=1, sort="craft"):
        # TODO MAKE FAST
        page = int(page)

        user = user_mod.User.query.filter_by(name="me").first()

        values = evaluation.get_values_for_user(user)

        # sort values
        values = sort_values(values, sort)

        # filter values to current page

        # make displays out of values

        displays = [CardValueDisplay(v) for v in values]  # TODO EXPENSIVE
        displays = sort_values(displays, sort)

        start, end = get_start_and_end_from_page(len(displays), page)
        displays_on_page = displays[start:end]

        displays_on_page = group_card_value_displays(displays_on_page)

        return flask.render_template('card_table.html', page=page, sort=sort, card_values=displays_on_page)
