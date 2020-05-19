"""Gets card values from a user's weighted deck searches"""
import typing as t

import pandas as pd

import models.deck_search
import models.rarity


def get_card_playabilities(
    weighted_deck_searches: t.List[models.deck_search.WeightedDeckSearch],
) -> models.deck_search.DeckSearchValue_DF:
    """Gets a dataframe of all cards with values for a user
      based on all their weighted deck searches."""

    playabilities = [
        weighted_search.get_playabilities()
        for weighted_search in weighted_deck_searches
    ]
    summed_playabilities = models.deck_search.PlayabilityFrame.concat(playabilities)
    summed_playabilities.normalize()
    return summed_playabilities
