"""This is where the routes are defined."""
import typing as t

import numpy as np
import pandas as pd

from card_evaluation import OwnValueFrame
from card_frame_bases import CardDetails
import models.card
import models.user
from views.card_values import display_filters


# TODO Tests :(


class CardDisplays:
    """Handles sorting and filtering a list of CardValueDisplay to serve."""

    CARDS_PER_PAGE = 24

    def __init__(self, value_info: OwnValueFrame):
        self.value_info = value_info
        self.is_filtered = False
        self.is_sorted = False

        self._sort_method: t.Optional[display_filters.CardDisplaySort] = None
        self._ownership: t.Optional[display_filters.OwnershipFilter] = None

    @classmethod
    def make_for_user(cls, user: models.user.User, card_details: CardDetails):
        """Makes the cards for a user, cached for immediate reuse."""
        own_value = OwnValueFrame.from_user(user, card_details)
        return cls(own_value)

    @property
    def sort_method(self) -> t.Optional[display_filters.CardDisplaySort]:
        return self._sort_method

    @sort_method.setter
    def sort_method(self, value):
        if self._sort_method != value:
            self.is_sorted = False
            self.is_filtered = False
            self._sort_method = value

    @property
    def ownership(self) -> t.Optional[display_filters.OwnershipFilter]:
        return self._ownership

    @ownership.setter
    def ownership(self, value):
        if self._ownership != value:
            self.is_sorted = False
            self.is_filtered = False
            self._ownership = value

    def get_page(self, page_num: int = 0) -> OwnValueFrame:
        """Gets the page of card displays,
        sorting by the current sort method."""
        card_display_page_generator = CardDisplayPage(
            self.value_info, page_num=page_num, cards_per_page=self.CARDS_PER_PAGE
        )
        displays_on_page = card_display_page_generator.run()
        return displays_on_page

    def get_card(self, card_id: models.card.CardId) -> pd.DataFrame:
        """Gets all displays matching the given card id
        1 display for each playset size."""
        displays_df = self.value_info.df[
            np.logical_and(
                self.value_info.df[self.value_info.SET_NUM] == card_id.set_num,
                self.value_info.df[self.value_info.CARD_NUM] == card_id.card_num,
            )
        ]

        return displays_df

    def configure(
        self,
        sort_method: t.Type[display_filters.CardDisplaySort],
        ownership: t.Type[display_filters.OwnedFilter] = None,
    ) -> "CardDisplays":
        """Sets sort method and ownership filter,
        and updates displays to match."""
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
        if not self.is_filtered:
            filtered = self.value_info
            filtered = self.sort_method.filter(filtered)
            filtered = self.ownership.filter(filtered)

            self.value_info = filtered
            self.is_filtered = True

    def _sort(self):
        """Sorts displays by the given method"""
        if not self.is_sorted:
            sort_method = self.sort_method
            self.value_info = sort_method.sort(self.value_info)
            self.is_sorted = True


class CardDisplayPage:
    """Class for getting card displays for a given page."""

    INDEX_KEYS = [OwnValueFrame.SET_NUM_NAME, OwnValueFrame.CARD_NUM_NAME]

    def __init__(self, value_info, page_num, cards_per_page=30):
        self.value_info = value_info
        self.cards_per_page = cards_per_page
        self.page_num = self._wrap_negative_page_num(page_num)

    def run(self) -> OwnValueFrame:
        """Call for the card displays to be displayed at the given page."""
        start_index = self._get_start_card_index()
        displays_on_page = OwnValueFrame(
            self.value_info.user,
            self.value_info[start_index : start_index + self.cards_per_page],
        )
        # displays_on_page = self._group_page(displays_on_page)
        return displays_on_page

    def _wrap_negative_page_num(self, page_num) -> int:
        num_pages = int(len(self.value_info) / self.cards_per_page)
        if page_num < 0:
            page_num = num_pages + page_num + 1
        return page_num

    def _get_start_card_index(self) -> int:
        """Gets the first and last card indices to render
        on the given page number."""

        start = self.page_num * self.cards_per_page
        return start

    @staticmethod
    def _group_page(page: OwnValueFrame) -> OwnValueFrame:  # todo make less disgusting
        """Groups the card value displays in the list as a single item.

        Grouped displays are given new minimum and maximum attributes
        representing the cards minimum and maximum counts in the list."""

        min_max_page = CardDisplayPage._get_min_max_of_page(page)

        min_max_dropped_duplicates = min_max_page.drop_duplicates()

        min_max_dropped_index_duplicates = min_max_dropped_duplicates[
            ~min_max_dropped_duplicates.index.duplicated(keep="first")
        ]

        reindexed = page.set_index(CardDisplayPage.INDEX_KEYS)
        deduplicated_index = reindexed[~reindexed.index.duplicated(keep="first")].index
        original_order = min_max_dropped_index_duplicates.reindex(
            index=deduplicated_index
        )

        reset_original_order = original_order.reset_index()
        no_duplicates = reset_original_order.drop_duplicates(
            subset=CardDisplayPage.INDEX_KEYS
        )

        return no_duplicates

    @staticmethod
    def _get_min_max_of_page(page):
        reindexed = page.set_index(CardDisplayPage.INDEX_KEYS)

        min_count, max_count = CardDisplayPage._get_page_min_max_counts(page)

        min_page = reindexed.join(min_count, rsuffix="_min")
        min_max_page = min_page.join(max_count, rsuffix="_max")
        del min_max_page[page.COUNT_IN_DECK_NAME]
        del min_max_page[page.PLAY_VALUE_NAME]
        del min_max_page[page.OWN_VALUE_NAME]
        del min_max_page[page.PLAY_CRAFT_EFFICIENCY_NAME]

        return min_max_page

    @staticmethod
    def format_ungrouped_page(page: pd.DataFrame) -> pd.DataFrame:
        """Formats a page for presentation without grouping it."""

        min_max_page = CardDisplayPage._get_min_max_of_page(page).reset_index()

        min_max_dropped_duplicates = min_max_page.drop_duplicates(
            subset=[page.SET_NUM_NAME, page.CARD_NUM_NAME, "count_in_deck_min"]
        )
        min_max_dropped_duplicates["count_in_deck_max"] = min_max_dropped_duplicates[
            "count_in_deck_min"
        ]
        return min_max_dropped_duplicates

    @staticmethod
    def _get_page_min_max_counts(page):
        grouped = page.groupby(page.index)
        index_columns = grouped[[page.SET_NUM_NAME, page.CARD_NUM_NAME]].first()
        measure_columns = grouped[
            [
                page.COUNT_IN_DECK_NAME,
                page.PLAY_VALUE_NAME,
                page.PLAY_CRAFT_EFFICIENCY_NAME,
            ]
        ]
        min_count = (
            measure_columns.min()
            .join(index_columns)
            .set_index(CardDisplayPage.INDEX_KEYS)
        )
        max_count = (
            measure_columns.max()
            .join(index_columns)
            .set_index(CardDisplayPage.INDEX_KEYS)
        )
        return min_count, max_count
