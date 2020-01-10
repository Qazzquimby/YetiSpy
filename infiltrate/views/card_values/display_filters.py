import typing
from abc import ABC

import numpy as np
import pandas as pd

import models.card
import models.card_set
import models.user
import profiling


def is_owned(display: pd.Series, user: models.user.User) -> bool:
    """Does the user own the amount of the card given by the display"""
    # TODO This is going to be slow.
    card_id = models.card.CardId(display['set_num'], display['card_num'])
    return models.user.collection.user_has_count_of_card(user, card_id, display['count_in_deck'])


class Filter(ABC):
    """ABC for methods of filtering cards to be displayed."""

    def __init__(self):
        pass

    @classmethod
    def filter(cls, cards: pd.DataFrame, user: models.user.User) -> bool:
        """Should the card be filtered out."""
        raise NotImplementedError


class OwnershipFilter(Filter, ABC):
    """Filters out cards based on ownership."""


class UnownedFilter(OwnershipFilter):
    """Keeps only unowned cards."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def filter(cls, cards: pd.DataFrame, user: models.user.User) -> pd.DataFrame:
        filtered = cards[cards['is_owned'] == False]
        return filtered


class OwnedFilter(OwnershipFilter):
    """Keeps only owned cards."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def filter(cls, cards: pd.DataFrame, user: models.user.User) -> pd.DataFrame:
        filtered = cards[cards['is_owned'] == True]
        return filtered


class AllFilter(OwnershipFilter):
    """Does not filter cards at all."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def filter(cls, cards: pd.DataFrame, user: models.user.User) -> pd.DataFrame:
        return cards


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
    def filter(cls, cards: pd.DataFrame, user: models.user.User) -> pd.DataFrame:
        return cards


class CraftSort(CardDisplaySort):
    """Sorts and filters cards to show craft efficiency."""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(displays: pd.DataFrame) -> pd.DataFrame:
        """Sorts the cards by highest to lowest card value per shiftstone crafting cost."""
        sorted = displays.sort_values(by=['value_per_shiftstone'], ascending=False)
        return sorted

    @classmethod
    def filter(cls, cards: pd.DataFrame, user: models.user.User) -> pd.DataFrame:
        """Filters out uncraftable."""
        filtered = cards[np.logical_not(models.card_set.is_campaign(cards['set_num']))]
        return filtered


class ValueSort(CardDisplaySort):
    """Sorts and filters cards to show overall card value"""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(displays: pd.DataFrame) -> pd.DataFrame:
        """Sorts cards from highest to lowest card value."""
        sorted = displays.sort_values(by=['value'], ascending=False)
        return sorted

    @classmethod
    def filter(cls, cards: pd.DataFrame, user: models.user.User) -> pd.DataFrame:
        """Excludes owned cards."""
        return cards


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


def create_is_owned_column(df: pd.DataFrame, user: models.user.User) -> pd.DataFrame:
    profiling.start_timer("create is_owned column")
    new_df = df.copy()
    new_df['is_owned'] = df.apply(lambda x: is_owned(x, user), axis=1)  # todo speed
    profiling.end_timer("create is_owned column")
    return new_df
