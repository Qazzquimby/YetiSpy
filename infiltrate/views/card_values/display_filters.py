import typing
from abc import ABC

import pandas as pd

import card_display
import models.card
import models.card_sets
import models.user


class Filter(ABC):
    """ABC for methods of filtering cards to be displayed."""

    def __init__(self):
        pass

    @classmethod
    def should_include_card(cls, display: card_display.CardValueDisplay, user: models.user.User) -> bool:
        """Should the card be filtered out."""
        raise NotImplementedError


class OwnershipFilter(Filter, ABC):
    """Filters out cards based on ownership."""

    @staticmethod
    def is_owned(display: card_display.CardValueDisplay, user) -> bool:
        """Does the user own the amount of the card given by the display"""
        card_id = models.card.CardId(display.card.set_num, display.card.card_num)
        return models.user.collection.user_has_count_of_card(user, card_id, display.count)


class UnownedFilter(OwnershipFilter):
    """Keeps only unowned cards."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def should_include_card(cls, display: card_display.CardValueDisplay, user: models.user.User) -> bool:
        return not cls.is_owned(display, user)


class OwnedFilter(OwnershipFilter):
    """Keeps only owned cards."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def should_include_card(cls, display: card_display.CardValueDisplay, user: models.user.User) -> bool:
        return cls.is_owned(display, user)


class AllFilter(OwnershipFilter):
    """Does not filter cards at all."""

    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def should_include_card(cls, display: card_display.CardValueDisplay, user: models.user.User) -> bool:
        return True


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
    def should_include_card(cls, display: card_display.CardValueDisplay, user: models.user.User) -> bool:
        return True


class CraftSort(CardDisplaySort):
    """Sorts and filters cards to show craft efficiency."""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(displays: pd.DataFrame) -> pd.DataFrame:
        """Sorts the cards by highest to lowest card value per shiftstone crafting cost."""
        return displays.sort_values(by=['value_per_shiftstone'], ascending=False)

    @classmethod
    def should_include_card(cls, display: card_display.CardValueDisplay, user: models.user.User) -> bool:
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
    def should_include_card(cls, display: card_display.CardValueDisplay, user: models.user.User) -> bool:
        """Excludes owned cards."""
        return True


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
