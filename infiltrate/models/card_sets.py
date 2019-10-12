"""Models for sets of cards."""
import numpy as np


@np.vectorize
def is_campaign(set_num: int):
    """Returns if the card set belongs to a campaign"""
    return 1000 < set_num
