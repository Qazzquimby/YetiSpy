"""This is where the routes are defined."""
import typing

import flask
from flask_classy import FlaskView

import infiltrate.card_display
from infiltrate import evaluation
from infiltrate import models
from infiltrate.card_display import CardValueDisplay


def group_card_value_displays(displays: typing.List[CardValueDisplay]):
    """Groups the card value displays in the list as a single item.

     Grouped displays are given new minimum and maximum attributes representing
    representing the cards minimum and maximum counts in the list."""

    def _get_minimum_count(card):
        return min([d.count for d in displays if d.card.name == card.name])

    def _get_maximum_count(card):
        return max([d.count for d in displays if d.card.name == card.name])

    def _remove_duplicates(displays: typing.List[CardValueDisplay]):
        names = [d.card.name for d in displays]
        first_indexes = set([names.index(name) for name in names])

        new_displays = []
        for i, card in enumerate(displays):
            if i in first_indexes:
                new_displays.append(card)
        return new_displays

    minimum_counts = {}
    maximum_counts = {}
    for display in displays:
        card = display.card
        if card.name not in maximum_counts.keys():
            minimum_counts[card.name] = _get_minimum_count(card)
            maximum_counts[card.name] = _get_maximum_count(card)

    displays = _remove_duplicates(displays)
    for display in displays:
        card = display.card
        display.minimum = minimum_counts[card.name]
        display.maximum = maximum_counts[card.name]

    return displays


def filter_displays(displays: typing.List[infiltrate.card_display.CardValueDisplay], user: models.user.User, sort: str):
    """Returns a list of displays filtered to match the given sort

    Craft sort does not contain campaign cards
    """
    filtered_displays = []

    for display in displays:
        if len(filtered_displays) > CARDS_PER_PAGE:
            break

        # TODO refactor this
        if sort == "craft":
            if models.card_sets.is_campaign(display.card.set_num):
                continue

        card_id = models.card.CardId(display.card.set_num, display.card.card_num)
        if models.user.user_has_count_of_card(user, card_id, display.count):
            continue

        filtered_displays.append(display)

    return filtered_displays


def sort_displays(displays: typing.List[CardValueDisplay], sort: str):
    """Returns a list of displays sorted by the given method."""
    if sort == "value":
        key = "value"
    elif sort == "craft":
        key = "value_per_shiftstone"

    return sorted(displays, key=lambda x: x.__dict__[key], reverse=True)


def get_displays_starting_on_page(displays: typing.List[CardValueDisplay], page: int):
    start = get_start_card_indices_from_page(len(displays), page)
    return displays[start:]


CARDS_PER_PAGE = 30


def get_start_card_indices_from_page(num_cards, page):
    """Gets the first and last card indices to render on the given page number."""
    num_pages = int(num_cards / CARDS_PER_PAGE)
    if page < 0:
        page = num_pages + page + 1
    start = page * CARDS_PER_PAGE
    return start


SORTS = ("craft", "value")


# noinspection PyMethodMayBeStatic
class CardsView(FlaskView):
    """View for the list of card values"""
    route_base = '/'

    def index(self):
        """The main card values page"""
        # TODO Refactor views
        # TODO search for card
        # TODO show number to buy with icons. Filled card for owned, Gold card for buy, Empty for dont

        # TODO make faster
        # TODO Tests :(

        # TODO import collection from EW api
        # TODO host on AWS
        # TODO support user sign in

        # TODO figure out card sets and purchaes
        # TODO improve craft efficiency by taking into account drop rate

        return flask.render_template("card_values.html")

    def card_values(self, page=1, sort="craft"):
        """A table loaded into index. Not accessed by the user."""
        page = int(page)

        user = models.user.User.query.filter_by(name="me").first()
        displays = evaluation.get_displays_for_user(user)

        # displays = filter_displays(displays, sort)
        displays = sort_displays(displays, sort)

        displays_starting_on_page = get_displays_starting_on_page(displays, page)

        displays_on_page = filter_displays(displays_starting_on_page, user, sort)

        displays_on_page = group_card_value_displays(displays_on_page)

        return flask.render_template('card_table.html', page=page, sort=sort, card_values=displays_on_page)
