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
import pandas as pd
import typing as t

from models.deck_search import DeckSearchHasCard, WeightedDeckSearch


class CardCopyFrame:
    SET_NUM = "set_num"
    CARD_NUM = "card_num"
    COUNT_IN_DECK = "count_in_deck"

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __eq__(self, other):
        return type(self) == type(other) and self.df.equals(other.df)


class PlayCountFrame(CardCopyFrame):
    """Has column PlayCount representing the number of decks containing
    the weighted count of that card in decks of all deck searches"""

    NUM_DECKS_COL = "num_decks_with_count_or_less"

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
        play_count_df[cls.NUM_DECKS_COL] *= weighted_deck_search.weight
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
