"""Models for sets of cards."""


def is_campaign(set_num: int):
    """Returns if the card set belongs to a campaign"""
    return 1000 < set_num
