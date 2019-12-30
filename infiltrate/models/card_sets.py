"""Models for sets of cards."""
import numpy as np

import models.card


@np.vectorize
def is_campaign(set_num: int):
    """Return if the card set belongs to a campaign"""
    return 1000 < set_num


def get_main_sets():
    sets = get_sets()
    # noinspection PyTypeChecker
    main_sets = sets[np.logical_not(is_campaign(sets))]
    return main_sets


def get_newest_main_set():
    """Gets the newest droppable pack."""
    main_sets = get_main_sets()
    newest_main_set = main_sets[-1]
    return newest_main_set


def get_old_main_sets():
    """Gets droppable packs that are not the newest set."""
    main_sets = get_main_sets()
    newest_main_set = main_sets[:-1]
    return newest_main_set


def get_sets() -> np.array:
    """Return array of card set ids."""
    set_nums = list(models.card.db.session.query(models.card.Card.set_num).distinct())
    set_nums = [s[0] for s in set_nums]
    set_nums = np.array(set_nums)
    return set_nums
