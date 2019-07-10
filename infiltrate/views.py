"""This is where the routes are defined."""
from __future__ import annotations

import typing
from abc import ABC

import flask
import pandas as pd
from flask_classy import FlaskView

from infiltrate import evaluation, caches
from infiltrate import models
from infiltrate.card_display import CardValueDisplay
from infiltrate.models.card import CardDisplay


# TODO Tests :(
# TODO search for card
# TODO show number to buy with icons. Filled card for owned, Gold card for buy, Empty for dont
# TODO make faster
# TODO import collection from EW api
# TODO host on AWS
# TODO support user sign in

# TODO figure out card sets and purchases
# TODO improve craft efficiency by taking into account drop rate

class Filter(ABC):
    def __init__(self):
        pass

    @classmethod
    def should_include_card(cls, display: CardValueDisplay, user: models.user.User) -> bool:
        """Should the card be filtered out."""
        raise NotImplementedError


class OwnershipFilter(Filter, ABC):
    """Filters out cards based on ownership."""

    @staticmethod
    def is_owned(display: CardValueDisplay, user) -> bool:
        """Does the user own the amount of the card given by the display"""
        card_id = models.card.CardId(display.card.set_num, display.card.card_num)
        return models.user.user_has_count_of_card(user, card_id, display.count)


class UnownedFilter(OwnershipFilter):
    """Keeps only unowned cards."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def should_include_card(cls, display: CardValueDisplay, user: models.user.User) -> bool:
        return not cls.is_owned(display, user)


class OwnedFilter(OwnershipFilter):
    """Keeps only owned cards."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def should_include_card(cls, display: CardValueDisplay, user: models.user.User) -> bool:
        return cls.is_owned(display, user)


class AllFilter(OwnershipFilter):
    """Does not filter cards at all."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def should_include_card(cls, display: CardValueDisplay, user: models.user.User) -> bool:
        return True


# noinspection PyMissingOrEmptyDocstring
class CardDisplaySort(Filter, ABC):
    """A method of sorting and filtering cards displays."""

    def __init__(self):
        super().__init__()

    @property
    def default_ownership(self) -> typing.Type[OwnershipFilter]:
        return UnownedFilter

    @staticmethod
    def sort(displays: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @classmethod
    def should_include_card(cls, display: CardValueDisplay, user: models.user.User) -> bool:
        return True


class CraftSort(CardDisplaySort):
    """Sorts and filters cards to show craft efficiency."""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(displays: pd.DataFrame) -> pd.DataFrame:
        """Sorts the cards by highest to lowest card value per shiftstone crafting cost."""
        # return sorted(displays, key=lambda x: x.value_per_shiftstone, reverse=True)

        return displays.sort_values(by=['value_per_shiftstone'], ascending=False)

    @classmethod
    def should_include_card(cls, display: CardValueDisplay, user: models.user.User) -> bool:
        """Filters out uncraftable and owned cards."""

        is_campaign = models.card_sets.is_campaign(display.card.set_num)
        return not is_campaign


class ValueSort(CardDisplaySort):
    """Sorts and filters cards to show overall card value"""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(displays: pd.DataFrame) -> pd.DataFrame:
        """Sorts cards from highest to lowest card value."""
        # return sorted(displays, key=lambda x: x.value, reverse=True)
        return displays.sort_values(by=['value'], ascending=False)

    @classmethod
    def should_include_card(cls, display: CardValueDisplay, user: models.user.User) -> bool:
        """Excludes owned cards."""
        return True


class CardDisplays:
    """Handles sorting and filtering a list of CardValueDisplay to serve."""
    CARDS_PER_PAGE = 30

    def __init__(self, user: models.user.User):
        self.user = user
        self.raw_displays: pd.DataFrame = self.get_raw_displays()
        self.displays: pd.DataFrame = self.raw_displays[:]

        self.filtered_displays: typing.Optional[pd.DataFrame] = None
        self.is_filtered = False

        self.sorted_displays: typing.Optional[pd.DataFrame] = None
        self.is_sorted = False

        self.sort_method: typing.Optional[CardDisplaySort] = None
        self.ownership: typing.Optional[OwnershipFilter] = None

    def get_raw_displays(self):
        """Get all displays for a user, not sorted or filtered."""
        displays = evaluation.get_displays_for_user(self.user)
        displays = [display.to_dict() for display in displays]

        return pd.DataFrame(displays)

    def reset(self):
        """Undoes any processing such as sorting or filtering"""
        self.displays: pd.DataFrame = self.raw_displays.copy()

    def configure(self,
                  sort_method: typing.Type[CardDisplaySort],
                  ownership: typing.Type[OwnedFilter] = None) -> CardDisplays:
        """Sets sort method and ownership filter, and updates displays to match."""
        if not ownership:
            self.ownership = sort_method.default_ownership

        if self.sort_method != sort_method:
            self.is_sorted = False
            self.is_filtered = False
            self.sort_method = sort_method

        if self.ownership != ownership:
            self.is_filtered = False
            self.ownership = ownership
        self._process_displays()
        return self

    def _process_displays(self):
        """Sorts and filters the displays"""
        self._filter()
        self._sort()

    def _sort(self):
        """Sorts displays by the given method"""
        if not self.is_sorted:
            self.displays = self.sort_method.sort(self.displays)
            self.is_sorted = True

    def _filter(self):

        def should_include(series: pd.Series):
            display = CardValueDisplay.from_series(series)
            return self._should_include_display(display)

        if not self.is_filtered:
            filtered = self.displays[self.displays.apply(lambda x: should_include(x), axis=1)]
            self.displays = filtered
            self.is_filtered = True

    def get_page(self, page_num: int = 0) -> typing.List[CardValueDisplay]:
        """Gets the page of card displays, sorting by the current sort method."""
        displays_on_page = self._get_displays_on_page(page_num)
        displays_on_page = self._group_page(displays_on_page)
        return displays_on_page

    def _get_displays_on_page(self, page_num: int) -> typing.List[CardValueDisplay]:
        start_index = self._get_start_card_index_from_page(page_num)
        displays_on_page_df: pd.DataFrame = self.displays[start_index:start_index + self.CARDS_PER_PAGE]

        displays_on_page = [CardValueDisplay.from_series(row) for index, row in displays_on_page_df.iterrows()]

        return displays_on_page

    def _should_include_display(self, display: CardValueDisplay):
        sort_include = self.sort_method.should_include_card(display, self.user)
        own_include = self.ownership.should_include_card(display, self.user)
        return sort_include and own_include

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


@caches.mem_cache.cache("card_displays_for_user", expires=120)
def make_card_displays(user: models.user.User) -> CardDisplays:
    return CardDisplays(user)


def get_sort(sort_str):
    """Get an OwnershipFilter from its id string."""
    sort_str_to_sort = {'craft': CraftSort,
                        'value': ValueSort}

    sort = sort_str_to_sort.get(sort_str, None)
    if not sort:
        raise ValueError(f"Sort method {sort_str} not recognized. Known sorts are {sort_str_to_sort.keys()}")
    return sort


def get_owner(owner_str):
    """Get an OwnershipFilter from its id string."""
    owner_str_to_owner = {'unowned': UnownedFilter,
                          'owned': OwnedFilter,
                          'all': AllFilter}

    sort = owner_str_to_owner.get(owner_str, None)
    if not sort:
        raise ValueError(f"Ownership type {owner_str} not recognized. Known types are {owner_str_to_owner.keys()}")
    return sort


# noinspection PyMethodMayBeStatic
class CardsView(FlaskView):
    """View for the list of card values"""
    route_base = '/'

    def index(self):
        """The main card values page"""
        return flask.render_template("card_values.html")

    def card_values(self, page_num=1, sort_str="craft", owner_str=None):
        """A table loaded into index. Not accessed by the user."""
        page_num = int(page_num)
        sort = get_sort(sort_str)
        if not owner_str:
            owner = sort.default_ownership
        else:
            owner = get_owner(owner_str)

        user = models.user.User.query.filter_by(name="me").first()
        displays = make_card_displays(user).configure(sort, owner)

        page = displays.get_page(page_num)

        return flask.render_template('card_values_table.html', page=page_num, sort=sort_str, card_values=page)

    def card_search(self, search_str='_'):
        search_str = search_str[1:]

        matching_card = models.card.ALL_CARDS.get_matching_card(search_str)

        return matching_card
