"""This is where the routes are defined."""
# TODO search for card
# TODO show number to buy with icons. Filled card for owned, Gold card for buy, Empty for dont

# TODO make faster
# TODO Tests :(

# TODO import collection from EW api
# TODO host on AWS
# TODO support user sign in

# TODO figure out card sets and purchases
# TODO improve craft efficiency by taking into account drop rate
import abc
import typing

import flask
from flask_classy import FlaskView

from infiltrate import evaluation
from infiltrate import models
from infiltrate.card_display import CardValueDisplay
from infiltrate.models.card import CardDisplay


# noinspection PyMissingOrEmptyDocstring
class CardDisplaySort(abc.ABC):
    """A method of sorting and filtering cards displays."""

    def __init__(self):
        pass

    @staticmethod
    def sort(displays: typing.List[CardValueDisplay]):
        raise NotImplementedError

    @staticmethod
    def should_exclude_card(display: CardValueDisplay, user: models.user.User):
        raise NotImplementedError

    @staticmethod
    def is_owned(display: CardValueDisplay, user):
        card_id = models.card.CardId(display.card.set_num, display.card.card_num)
        return models.user.user_has_count_of_card(user, card_id, display.count)


class CraftSort(CardDisplaySort):
    """Sorts and filters cards to show craft efficiency."""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(displays: typing.List[CardValueDisplay]):
        """Sorts the cards by highest to lowest card value per shiftstone crafting cost."""
        return sorted(displays, key=lambda x: x.value_per_shiftstone, reverse=True)

    @staticmethod
    def should_exclude_card(display: CardValueDisplay, user: models.user.User):
        """Filters out uncraftable and owned cards."""
        is_campaign = models.card_sets.is_campaign(display.card.set_num)
        is_owned = super().is_owned(display, user)
        return is_campaign or is_owned


class ValueSort(CardDisplaySort):
    """Sorts and filters cards to show overall card value"""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(displays: typing.List[CardValueDisplay]):
        """Sorts cards from highest to lowest card value."""
        return sorted(displays, key=lambda x: x.value, reverse=True)

    @staticmethod
    def should_exclude_card(display: CardValueDisplay, user: models.user.User):
        """Excludes owned cards."""
        # TODO filter owned should really be toggleable.
        is_owned = super().is_owned(display, user)
        return is_owned


SORT_STR_TO_SORT = {'craft': CraftSort,
                    'value': ValueSort}


class CardDisplays:
    """Handles sorting and filtering a list of CardValueDisplay to serve."""
    CARDS_PER_PAGE = 30

    def __init__(self, user: models.user.User):
        self.user = user
        self.raw_displays = self.get_raw_displays()

        self.displays = self.raw_displays[:]
        self.sort_method = None

    def get_raw_displays(self):
        """Get all displays for a user, not sorted or filtered."""
        return evaluation.get_displays_for_user(self.user)

    def reset(self):
        """Undoes any processing such as sorting or filtering"""
        self.displays = self.raw_displays[:]

    def sort(self, sort_method: typing.Type[CardDisplaySort]):
        """Sorts displays by the given method"""
        if self.sort_method != sort_method:  # TODO make sure comparison is working
            self.sort_method = sort_method
            self.displays = self.sort_method.sort(self.displays)
        return self

    def get_page(self, page_num: int = 0) -> typing.List[CardValueDisplay]:
        """Gets the page of card displays, sorting by the current sort method."""
        displays_on_page = self._get_displays_on_page(page_num)
        displays_on_page = self._group_page(displays_on_page)
        return displays_on_page

    def _get_displays_on_page(self, page_num: int):
        start_index = self._get_start_card_index_from_page(page_num)

        displays_on_page = []
        for display in self.displays[start_index:]:
            if not self.sort_method.should_exclude_card(display, self.user):
                displays_on_page.append(display)

            if len(displays_on_page) > self.CARDS_PER_PAGE:
                break

        return displays_on_page

    def _get_start_card_index_from_page(self, page_num: int) -> int:
        """Gets the first and last card indices to render on the given page number."""
        num_pages = int(len(self.displays) / self.CARDS_PER_PAGE)
        if page_num < 0:
            page_num = num_pages + page_num + 1
        start = page_num * self.CARDS_PER_PAGE
        return start

    @staticmethod
    def _group_page(page: typing.List[CardValueDisplay]):
        """Groups the card value displays in the list as a single item.

         Grouped displays are given new minimum and maximum attributes representing
        representing the cards minimum and maximum counts in the list."""

        def _get_minimum_count(c: CardDisplay) -> int:
            return min([d.count for d in page if d.card.name == c.name])

        def _get_maximum_count(c: CardDisplay) -> int:
            return max([d.count for d in page if d.card.name == c.name])

        def _remove_duplicates(displays: typing.List[CardValueDisplay]):
            names = [d.card.name for d in displays]
            first_indexes = set([names.index(name) for name in names])

            new_displays = []
            for i, d in enumerate(displays):
                if i in first_indexes:
                    new_displays.append(d)
            return new_displays

        minimum_counts = {}
        maximum_counts = {}
        for display in page:
            card = display.card
            if card.name not in maximum_counts.keys():
                minimum_counts[card.name] = _get_minimum_count(card)
                maximum_counts[card.name] = _get_maximum_count(card)

        page = _remove_duplicates(page)
        for display in page:
            card = display.card
            display.minimum = minimum_counts[card.name]
            display.maximum = maximum_counts[card.name]

        return page


# noinspection PyMethodMayBeStatic
class CardsView(FlaskView):
    """View for the list of card values"""
    route_base = '/'

    def index(self):
        """The main card values page"""
        return flask.render_template("card_values.html")

    def card_values(self, page_num=1, sort_str="craft"):
        """A table loaded into index. Not accessed by the user."""
        page_num = int(page_num)
        sort = SORT_STR_TO_SORT.get(sort_str, None)
        if not sort:
            raise ValueError(f"Sort method {sort_str} not recognized. Known sorts are {SORT_STR_TO_SORT.keys()}")

        user = models.user.User.query.filter_by(name="me").first()
        displays = CardDisplays(user).sort(sort)
        displays.sort(sort)

        page = displays.get_page(page_num)

        return flask.render_template('card_table.html', page=page_num, sort=sort_str, card_values=page)
