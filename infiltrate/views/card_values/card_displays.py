"""This is where the routes are defined."""
import typing

import numpy as np
import pandas as pd

import caches
# TODO improve craft efficiency by taking into account drop rate
# TODO figure out card sets and purchases
import models.card
import models.card_set
import models.rarity
import models.user
import models.user.collection
import rewards
from views.card_values import display_filters


# TODO Tests :(


@pd.np.vectorize
def get_value_per_shiftstone(rarity_str: str, value: float):
    # todo cost could be calculated once per card rather than once per count
    cost = models.rarity.rarity_from_name[rarity_str].enchant
    value_per_shiftstone = value * 100 / cost
    return value_per_shiftstone


@pd.np.vectorize
def get_findability(rarity_str: str, set_num: models.card_set.CardSet):
    # todo cost could be calculated once per card rather than once per count
    player = rewards.DEFAULT_PLAYER  # TODO allow custom player profiles to override this.
    player: rewards.PlayerRewards

    rarity = models.rarity.rarity_from_name[rarity_str]
    findability = player.get_chance_of_specific_card_drop_in_a_week(rarity=rarity, card_set=set_num)
    return findability


class CardDisplays:
    """Handles sorting and filtering a list of CardValueDisplay to serve."""
    CARDS_PER_PAGE = 30

    def __init__(self, user: models.user.User, all_cards: models.card.AllCards):
        self.user = user
        self.raw_value_info: pd.DataFrame = self.get_value_info(all_cards)
        self.value_info: pd.DataFrame = self.raw_value_info[:]
        self.is_filtered = False
        self.is_sorted = False

        self._sort_method: typing.Optional[display_filters.CardDisplaySort] = None
        self._ownership: typing.Optional[display_filters.OwnershipFilter] = None

    @property
    def sort_method(self) -> typing.Optional[display_filters.CardDisplaySort]:
        return self._sort_method

    @sort_method.setter
    def sort_method(self, value):
        if self._sort_method != value:
            self.is_sorted = False
            self.is_filtered = False
            self._sort_method = value

    @property
    def ownership(self) -> typing.Optional[display_filters.OwnershipFilter]:
        return self._ownership

    @ownership.setter
    def ownership(self, value):
        if self._ownership != value:
            self.is_sorted = False
            self.is_filtered = False
            self._ownership = value

    def get_value_info(self, all_cards: models.card.AllCards):
        """Get all displays for a user, not sorted or filtered."""
        values: pd.DataFrame = self.user.get_values()
        if len(values) == 0:
            print("get_raw_values, no values found")
        values = values.set_index(['set_num', 'card_num']).join(all_cards.df.set_index(['set_num', 'card_num']))
        values['value_per_shiftstone'] = get_value_per_shiftstone(values['rarity'], values['value'])
        values = values.reset_index()

        # FINDABILITY todo make this work to different degrees based on player preference.
        card_classes = values[['set_num', 'rarity']].drop_duplicates()

        card_set = np.vectorize(models.card_set.get_set_from_set_num)(card_classes['set_num'])
        card_classes['findability'] = get_findability(card_classes['rarity'], card_set)
        values = (values.set_index(['set_num', 'rarity'])
                  .join(card_classes.set_index(['set_num', 'rarity']))
                  .reset_index())
        values['value_per_shiftstone'] *= 1 - values['findability']
        values = display_filters.create_is_owned_column(values, self.user)
        return values

    def get_page(self, page_num: int = 0) -> pd.DataFrame:
        """Gets the page of card displays, sorting by the current sort method."""
        displays_on_page = CardDisplayPage(self.value_info, page_num=page_num)()
        return displays_on_page

    def get_card(self, card_id: models.card.CardId) -> pd.DataFrame:
        """Gets all displays matching the given card id (1 display for each playset size)."""
        displays_df = self.value_info[np.logical_and(self.value_info['set_num'] == card_id.set_num,
                                                     self.value_info['card_num'] == card_id.card_num)]

        return displays_df

    def configure(self,
                  sort_method: typing.Type[display_filters.CardDisplaySort],
                  ownership: typing.Type[display_filters.OwnedFilter] = None) -> 'CardDisplays':
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
        """The card display represented by the series should not be filtered out."""

        if not self.is_filtered:
            filtered = self.raw_value_info
            filtered = self.sort_method.filter(filtered, self.user)
            filtered = self.ownership.filter(filtered, self.user)

            self.value_info = filtered
            # self._normalize_displays()
            self.is_filtered = True

    # def _normalize_displays(self):
    #     # todo I'm putting normalization much earlier so that purchases will correlate. This should be removed.
    #     max_value = max(self.value_info['value'].max(), 1)
    #     self.value_info = self.value_info.assign(value=lambda x: 100 * x['value'] / max_value)

    def _sort(self):
        """Sorts displays by the given method"""
        if not self.is_sorted:
            sort_method = self.sort_method
            self.value_info = sort_method.sort(self.value_info)
            self.is_sorted = True


class CardDisplayPage:  # TODO get rid of the __call__ system
    """Call for the card displays to be displayed at the given page."""

    def __init__(self, value_info, page_num, cards_per_page=30):
        self.value_info = value_info
        self.cards_per_page = cards_per_page
        self.page_num = self._wrap_negative_page_num(page_num)

    def __call__(self) -> pd.DataFrame:
        start_index = self._get_start_card_index()
        displays_on_page_df: pd.DataFrame = self.value_info[start_index:start_index + self.cards_per_page]
        displays_on_page = self._group_page(displays_on_page_df)
        return displays_on_page

    def _wrap_negative_page_num(self, page_num) -> int:
        num_pages = int(len(self.value_info) / self.cards_per_page)
        if page_num < 0:
            page_num = num_pages + page_num + 1
        return page_num

    def _get_start_card_index(self) -> int:
        """Gets the first and last card indices to render on the given page number."""

        start = self.page_num * self.cards_per_page
        return start

    @staticmethod
    def _group_page(page: pd.DataFrame) -> pd.DataFrame:  # todo make less disgusting
        """Groups the card value displays in the list as a single item.

         Grouped displays are given new minimum and maximum attributes representing
        representing the cards minimum and maximum counts in the list."""
        min_count = page.groupby(['set_num', 'card_num'])['count_in_deck', 'value', 'value_per_shiftstone'].min()
        max_count = page.groupby(['set_num', 'card_num'])['count_in_deck', 'value', 'value_per_shiftstone'].max()
        reindexed = page.set_index(['set_num', 'card_num'])
        reindexed_deduplicate = reindexed[~reindexed.index.duplicated(keep='first')]

        min_page = reindexed.join(min_count, rsuffix='_min')
        min_max_page = min_page.join(max_count, rsuffix='_max')
        del min_max_page['count_in_deck']
        del min_max_page['value']
        del min_max_page['value_per_shiftstone']
        min_max_dropped_duplicates = min_max_page.drop_duplicates()

        min_max_dropped_index_duplicates = min_max_dropped_duplicates[
            ~min_max_dropped_duplicates.index.duplicated(keep='first')]
        original_index = reindexed_deduplicate.index
        original_order = min_max_dropped_index_duplicates.reindex(index=original_index)

        original_index = original_order.reset_index()
        no_duplicates = original_index.drop_duplicates(subset=['set_num', 'card_num'])

        return no_duplicates

    @staticmethod
    def format_ungrouped_page(page: pd.DataFrame) -> pd.DataFrame:
        """Formats a page for presentation without grouping it."""
        # TODO this is pretty gross, and duplicates _group_page
        min_count = page.groupby(['set_num', 'card_num', 'count_in_deck'])[
            'count_in_deck', 'value', 'value_per_shiftstone'].min()
        max_count = page.groupby(['set_num', 'card_num', 'count_in_deck'])[
            'count_in_deck', 'value', 'value_per_shiftstone'].max()
        page.set_index(['set_num', 'card_num'], inplace=True)
        page = page.join(min_count, rsuffix='_min')
        page = page.join(max_count, rsuffix='_max')
        del page['count_in_deck']
        del page['value']
        del page['value_per_shiftstone']
        page.reset_index(inplace=True)
        page.drop_duplicates(subset=['set_num', 'card_num', 'count_in_deck'], inplace=True)

        return page


@caches.mem_cache.cache("card_displays_for_user", expires=120)
def make_card_displays(user: models.user.User, all_cards: models.card.AllCards) -> CardDisplays:
    """Makes the cards for a user, cached for immediate reuse."""
    return CardDisplays(user, all_cards)
