"""Gets card values from a user's weighted deck searches"""
import typing

import pandas as pd

import models.deck_search
import models.user


class CardValueDataframeGetter:
    """Callable to get a dataframe of all cards with the user's evaluations given their weighted deck searches."""

    def __init__(self, weighted_deck_searches: typing.List[models.deck_search.WeightedDeckSearch]):
        self.weighted_deck_searches = weighted_deck_searches

    def get_cards_values_df(self) -> models.deck_search.DeckSearchValue_DF:
        """Gets a dataframe of all cards with values for a user based on all their weighted deck searches."""
        value_dfs = self._get_individual_value_dfs()
        summed_value_df = self._merge_value_dfs(value_dfs)
        return summed_value_df

    def _get_individual_value_dfs(self) -> typing.List[models.deck_search.DeckSearchValue_DF]:
        """Get a list of ValueDicts for a user, each based on a single weighted deck search."""
        value_dfs = []
        for weighted_search in self.weighted_deck_searches:
            value_df = weighted_search.get_value_df()
            value_dfs.append(value_df)

        return value_dfs

    @staticmethod
    def _merge_value_dfs(value_dfs: typing.List[models.deck_search.DeckSearchValue_DF]) \
            -> models.deck_search.DeckSearchValue_DF:
        combined_value_dfs = pd.concat(value_dfs)
        summed_value_df = combined_value_dfs.groupby(['set_num', 'card_num', 'count_in_deck']).sum()
        summed_value_df.reset_index(inplace=True)
        return summed_value_df
