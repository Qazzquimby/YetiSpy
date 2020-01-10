"""Models for sets of cards."""
import typing
from collections.abc import Iterable

import numpy as np

import models.card


class CardSet:
    def __init__(self, set_nums=typing.Union[typing.List[int], int]):
        if isinstance(set_nums, Iterable):
            self.set_nums = set_nums
        else:
            self.set_nums = [set_nums]
            assert set_nums not in (0, 1)

    def __str__(self):
        return str(self.set_nums)


@np.vectorize
def is_campaign(set_num: int):
    """Return if the card set belongs to a campaign"""
    return 1000 < set_num


def get_set_nums() -> typing.List[int]:
    """Return card set ids."""
    set_nums = list(models.card.db.session.query(models.card.Card.set_num).distinct())
    set_nums = [s[0] for s in set_nums if s[0]]
    return set_nums


def get_set_from_set_num(set_num: int) -> CardSet:
    if set_num in (0, 1):
        return CardSet([0, 1])
    else:
        return CardSet([set_num])


def get_sets_from_set_nums(set_nums: typing.List[int]) -> typing.List[CardSet]:
    """Return card sets. Same as set ids, but 0 and 1 are one set."""
    card_sets = [get_set_from_set_num(s) for s in set_nums if s != 0]
    return card_sets


# def get_sets() -> typing.List[CardSet]:
#     """Return all card sets."""
#     set_nums = get_set_nums()
#     card_sets = get_sets_from_set_nums(set_nums)
#     return card_sets


def get_main_set_nums():
    sets = get_set_nums()
    main_sets = np.array(sets)[np.logical_not(is_campaign(sets))]
    return main_sets


def get_campaign_set_nums():
    sets = get_set_nums()
    campaign_sets = np.array(sets)[is_campaign(sets)]
    return campaign_sets


def get_newest_main_set():
    """Gets the newest droppable pack."""
    main_sets = get_main_set_nums()
    newest_main_set = main_sets[-1]
    return newest_main_set


def get_old_main_sets():
    """Gets droppable packs that are not the newest set."""
    main_sets = get_main_set_nums()
    newest_main_set = main_sets[:-1]
    return newest_main_set
