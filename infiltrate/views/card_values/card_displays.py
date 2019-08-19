"""This is where the routes are defined."""
from __future__ import annotations

import typing

import pandas as pd

import caches
# TODO figure out card sets and purchases
# TODO improve craft efficiency by taking into account drop rate
import card_display
import models.card
import models.card_sets
import models.user
import models.user.collection
# TODO Tests :(
# TODO host on AWS
from views.card_values.display_filters import CardDisplaySort, OwnedFilter, OwnershipFilter


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

        self._sort_method: typing.Optional[CardDisplaySort] = None
        self._ownership: typing.Optional[OwnershipFilter] = None

    @property
    def sort_method(self) -> typing.Optional[CardDisplaySort]:
        return self._sort_method

    @sort_method.setter
    def sort_method(self, value):
        if self._sort_method != value:
            self.is_sorted = False
            self.is_filtered = False
            self._sort_method = value

    @property
    def ownership(self) -> typing.Optional[OwnershipFilter]:
        return self._ownership

    @ownership.setter
    def ownership(self, value):
        if self._ownership != value:
            self.is_filtered = False
            self._ownership = value

    def get_raw_displays(self):
        """Get all displays for a user, not sorted or filtered."""
        displays = self.user.get_displays()
        displays = [display.to_dict() for display in displays]
        df = pd.DataFrame(displays)
        return df

    def get_page(self, page_num: int = 0) -> typing.List[card_display.CardValueDisplay]:
        """Gets the page of card displays, sorting by the current sort method."""
        displays_on_page = CardDisplayPage(self.displays, page_num=page_num)()
        return displays_on_page

    def get_card(self, card_id: models.card.CardId):
        """Gets all displays matching the given card id (1 display for each playset size)."""
        displays_df = self.displays[self.displays.apply(lambda x:
                                                        x["set_num"] == card_id.set_num
                                                        and x["card_num"] == card_id.card_num, axis=1)]
        displays = [card_display.CardValueDisplay.from_series(row) for index, row in displays_df.iterrows()]

        return displays

    def configure(self, sort_method: typing.Type[CardDisplaySort], ownership: typing.Type[OwnedFilter] = None) \
            -> CardDisplays:
        """Sets sort method and ownership filter, and updates displays to match."""
        if not ownership:
            self.ownership = sort_method.default_ownership

        self.sort_method = sort_method
        self.ownership = ownership

        self._process_displays()
        return self

    def _process_displays(self):
        """Sorts and filters the displays"""
        self._filter()
        self._sort()

    def _filter(self):

        def should_include(series: pd.Series):
            """The card display represented by the series should not be filtered out."""
            display = card_display.CardValueDisplay.from_series(series)
            return self._should_include_display(display)

        if not self.is_filtered:
            filtered = self.displays[self.displays.apply(lambda x: should_include(x), axis=1)]
            self.displays = filtered
            self._normalize_displays()
            self.is_filtered = True

    def _should_include_display(self, display: card_display.CardValueDisplay):
        sort_include = self.sort_method.should_include_card(display, self.user)
        own_include = self.ownership.should_include_card(display, self.user)
        return sort_include and own_include

    def _normalize_displays(self):
        for key in ["value"]:
            key_max = max(self.displays[key].max(), 1)
            self.displays[key] = 100 * self.displays[key] / key_max
            # todo check this

    #             """C:\Users\User\PycharmProjects\eternalCardEvaluator\infiltrate\views\card_values\card_displays.py:120: SettingWithCopyWarning:
    # A value is trying to be set on a copy of a slice from a DataFrame.
    # Try using .loc[row_indexer,col_indexer] = value instead
    #
    # See the caveats in the documentation: http://pandas.pydata.org/pandas-docs/stable/indexing.html#indexing-view-versus-copy
    #   self.displays[key] = 100 * self.displays[key] / key_max"""

    def _sort(self):
        """Sorts displays by the given method"""
        if not self.is_sorted:
            self.displays = self.sort_method.sort(self.displays)
            self.is_sorted = True


class CardDisplayPage:
    """Call for the card displays to be displayed at the given page."""

    def __init__(self, displays, page_num, cards_per_page=30):
        self.displays = displays
        self.cards_per_page = cards_per_page
        self.page_num = self._wrap_negative_page_num(page_num)

    def __call__(self) -> typing.List[card_display.CardValueDisplay]:
        start_index = self._get_start_card_index()
        displays_on_page_df: pd.DataFrame = self.displays[start_index:start_index + self.cards_per_page]

        displays_on_page = [card_display.CardValueDisplay.from_series(row) for index, row in
                            displays_on_page_df.iterrows()]
        displays_on_page = self._group_page(displays_on_page)
        return displays_on_page

    def _wrap_negative_page_num(self, page_num) -> int:
        num_pages = int(len(self.displays) / self.cards_per_page)
        if page_num < 0:
            page_num = num_pages + page_num + 1
        return page_num

    def _get_start_card_index(self) -> int:
        """Gets the first and last card indices to render on the given page number."""

        start = self.page_num * self.cards_per_page
        return start

    @staticmethod
    def _group_page(page: typing.List[card_display.CardValueDisplay]) -> typing.List[card_display.CardValueDisplay]:
        """Groups the card value displays in the list as a single item.

         Grouped displays are given new minimum and maximum attributes representing
        representing the cards minimum and maximum counts in the list."""

        def _get_min_count(c: models.card.CardDisplay) -> int:
            return min([d.count for d in page if d.card.name == c.name])

        def _get_max_count(c: models.card.CardDisplay) -> int:
            return max([d.count for d in page if d.card.name == c.name])

        def _remove_duplicates(displays: typing.List[card_display.CardValueDisplay]):
            names = [d.card.name for d in displays]
            first_indexes = set([names.index(name) for name in names])
            new_displays = []
            for i, d in enumerate(displays):
                if i in first_indexes:
                    new_displays.append(d)
            return new_displays

        min_max_counts = {}
        for display in page:
            card = display.card
            if card.name not in min_max_counts.keys():
                min_max_counts[card.name] = (_get_min_count(card), _get_max_count(card))

        page = _remove_duplicates(page)
        for display in page:
            card = display.card
            display.minimum, display.maximum = min_max_counts[card.name]

        return page


@caches.mem_cache.cache("card_displays_for_user", expires=120)
def make_card_displays(user: models.user.User) -> CardDisplays:
    """Makes the cards for a user, cached for immediate reuse."""
    return CardDisplays(user)
