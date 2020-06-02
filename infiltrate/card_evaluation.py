"""Contains Dataframe wrappers for additional analysis on card data.

Class Dependencies:
Play Counts (Weighted Deck Searches)
Play Rates (Play Counts)
Play Value (Play Rates, Collection Fit)
Play Craft Efficiency (Play Value, Findability, Cost)
Own Value (Play Value, Play Craft Efficiency)

Own Craft Efficiency (Own Value, Findability, Cost)
Purchase Efficiency (Own Value, Cost)
"""
import abc

import pandas as pd
import typing as t

import models.deck
from models.deck_search import DeckSearchHasCard, WeightedDeckSearch


class _CardCopyColumns(abc.ABC):
    """Holds dataframe of cards with copy #s to attach other information to"""

    SET_NUM = "set_num"
    CARD_NUM = "card_num"
    COUNT_IN_DECK = "count_in_deck"

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __eq__(self, other):
        return type(self) == type(other) and self.df.equals(other.df)


class _PlayCountColumns(_CardCopyColumns):
    PLAY_COUNT = "num_decks_with_count_or_less"


class PlayCountFrame(_PlayCountColumns):
    """Has column PLAY_COUNT representing the number of decks containing
    the weighted count of that card in decks of all deck searches"""

    @classmethod
    def from_weighted_deck_searches(
        cls, weighted_deck_searches: t.List[WeightedDeckSearch]
    ):
        """Build the dataframe from the list of weighted deck searches."""
        play_count_dfs: t.List[pd.DataFrame] = []
        for weighted_deck_search in weighted_deck_searches:
            play_count_dfs.append(cls._get_count_df(weighted_deck_search))

        combined = cls._sum_count_dfs(play_count_dfs)
        return cls(combined)

    @classmethod
    def _get_count_df(cls, weighted_deck_search: WeightedDeckSearch):
        """Get a dataframe representing the number of times a card is seen in
        decks in the deck search, times its weight."""
        play_count_df = DeckSearchHasCard.as_df(weighted_deck_search.deck_search_id)
        play_count_df[cls.PLAY_COUNT] *= weighted_deck_search.weight
        return play_count_df

    @classmethod
    def _sum_count_dfs(cls, play_count_dfs: t.List[pd.DataFrame]) -> pd.DataFrame:
        combined = pd.concat(play_count_dfs)
        summed = (
            combined.groupby([cls.SET_NUM, cls.CARD_NUM, cls.COUNT_IN_DECK])
            .sum()
            .reset_index()
        )
        return summed


class _PlayRateColumns(_PlayCountColumns):
    PLAY_RATE = "play_rate"


class PlayRateFrame(_PlayRateColumns):
    """Has column play_rate representing the fraction of decks containing the card
    in relevant deck searches."""

    @classmethod
    def from_play_counts(cls, play_count_frame: PlayCountFrame):
        """Constructor deriving play rates from play counts"""
        df = play_count_frame.df.copy()
        total_card_inclusions = sum(df[play_count_frame.PLAY_COUNT])
        df[cls.PLAY_RATE] = (
            df[cls.PLAY_COUNT]
            * models.deck.AVG_COLLECTABLE_CARDS_IN_DECK
            / total_card_inclusions
        )
        return cls(df)


class _PlayValueColumns(_PlayRateColumns):
    PLAY_VALUE = "play_value"


class PlayValueFrame(_PlayValueColumns):
    """Has column play_value representing how good it is to be able to play that card,
    on a scale of 0-100.
    This is very similar to own value, but doesn't account for reselling."""

    SCALE = 100

    @classmethod
    def from_play_rates(cls, play_rate_frame: PlayRateFrame):
        """Constructor deriving values from play rates."""
        # todo account for collection fit.
        df = play_rate_frame.df.copy()
        df[cls.PLAY_VALUE] = df[cls.PLAY_COUNT] * cls.SCALE / df[cls.PLAY_COUNT].max()
        return cls(df)
