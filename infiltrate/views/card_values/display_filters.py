import typing as t
from abc import ABC

import numpy as np

import infiltrate.models.card_set as card_set
import infiltrate.models.rarity as rarity_mod
from infiltrate.card_evaluation import OwnValueFrame


class Filter(ABC):
    """ABC for methods of filtering cards to be displayed."""

    def filter(self, cards: OwnValueFrame) -> OwnValueFrame:
        """Should the card be filtered out."""
        raise NotImplementedError


class OwnershipFilter(Filter, ABC):
    """Filters out cards based on ownership."""


class UnownedFilter(OwnershipFilter):
    """Keeps only unowned cards."""

    # noinspection PyMissingOrEmptyDocstring
    def filter(self, cards: OwnValueFrame):
        filtered_df = cards.query("is_owned == False")
        return OwnValueFrame(cards.user, filtered_df)


class OwnedFilter(OwnershipFilter):
    """Keeps only owned cards."""

    # noinspection PyMissingOrEmptyDocstring
    def filter(self, cards):
        filtered_df = cards.query("is_owned == True")
        return OwnValueFrame(cards.user, filtered_df)


class AllFilter(OwnershipFilter):
    """Does not filter cards at all."""

    # noinspection PyMissingOrEmptyDocstring
    def filter(self, cards):
        return cards


class CardDisplaySort(Filter, ABC):
    """A method of sorting and filtering cards displays."""

    def __init__(self):
        super().__init__()

    @property
    def default_ownership(self) -> t.Type[OwnershipFilter]:
        """The ownership filter to be used first, unless overridden."""
        return UnownedFilter

    @staticmethod
    def sort(displays: OwnValueFrame) -> OwnValueFrame:
        """The method to reorder the card displays."""
        raise NotImplementedError

    def filter(self, cards: OwnValueFrame) -> OwnValueFrame:
        """The method to filter out irrelevant card displays."""
        return cards


class CraftSort(CardDisplaySort):
    """Sorts and filters cards to show craft efficiency."""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(cards):
        """Sorts the cards by highest to lowest card value
         per shiftstone crafting cost."""
        cards.index.names = [name + "_index" for name in cards.index.names]
        sorted_df = cards.sort_values(
            by=[
                OwnValueFrame.PLAY_CRAFT_EFFICIENCY_NAME,
                OwnValueFrame.COUNT_IN_DECK_NAME,
            ],
            ascending=[False, True],
        )
        return OwnValueFrame(cards.user, sorted_df)

    def filter(self, cards):
        """Filters out uncraftable."""
        filtered_df = cards[
            np.logical_not(card_set.CardSet.is_campaign_from_num(cards.set_num))
        ]
        return OwnValueFrame(cards.user, filtered_df)


class ValueSort(CardDisplaySort):
    """Sorts and filters cards to show ownership card value"""

    def __init__(self):
        super().__init__()

    @staticmethod
    def sort(cards):
        """Sorts cards from highest to lowest card value."""
        cards.index.names = [name + "_index" for name in cards.index.names]
        sorted_df = cards.sort_values(
            by=[OwnValueFrame.PLAY_VALUE_NAME, OwnValueFrame.COUNT_IN_DECK_NAME],
            ascending=[False, True],
        )
        return OwnValueFrame(cards.user, sorted_df)

    def filter(self, cards):
        """Excludes owned cards."""
        return cards


EFFICIENCY_SORT = "efficiency"
VALUE_SORT = "value"


def get_sort(sort_str):
    """Get an OwnershipFilter from its id string."""
    sort_str_to_sort = {EFFICIENCY_SORT: CraftSort, VALUE_SORT: ValueSort}

    sort = sort_str_to_sort.get(sort_str, None)
    if sort is None:
        raise ValueError(
            f"Sort method {sort_str} not recognized. "
            f"Known sorts are {sort_str_to_sort.keys()}"
        )
    return sort


UNOWNED_FILTER = "unowned"
OWNED_FILTER = "owned"
ALL_FILTER = "all"


def get_ownership_filter(filter_str: str) -> Filter:
    """Get an OwnershipFilter from its id string."""
    filter_dict = {
        UNOWNED_FILTER: UnownedFilter(),
        OWNED_FILTER: OwnedFilter(),
        ALL_FILTER: AllFilter(),
    }
    return _get_filter(filter_dict=filter_dict, filter_str=filter_str)


class RarityFilter(OwnershipFilter):
    """Excludes the given rarity."""

    def __init__(self, rarity_name: str):
        self.rarity = rarity_mod.rarity_from_name[rarity_name]

    def filter(self, cards):
        filtered_df = cards[cards["rarity"] != self.rarity]
        return OwnValueFrame(cards.user, filtered_df)


def get_rarity_filter(filter_str: str) -> Filter:
    filter_dict = {
        rarity_name: RarityFilter(rarity_name)
        for rarity_name in rarity_mod.rarity_from_name.keys()
    }
    return _get_filter(filter_dict=filter_dict, filter_str=filter_str)


def _get_filter(filter_dict: t.Dict[str, Filter], filter_str: str) -> Filter:
    _filter = filter_dict.get(filter_str, None)
    if not _filter:
        raise KeyError(
            f"Filter {filter_str} not recognized. "
            f"Known filters are {filter_dict.keys()}"
        )
    return _filter
