"""Gets card values from a user's weighted deck searches"""
import typing

import pandas as pd

import card_collections
import models.card
import models.deck_search
import models.user


class GetCardValueDataframe:
    """Callable to get a dataframe of all cards with the user's evaluations given their weighted deck searches."""

    def __init__(self, weighted_deck_searches: typing.List[models.deck_search.WeightedDeckSearch]):
        self.weighted_deck_searches = weighted_deck_searches

    def __call__(self):  # todo don't use callable class functions as a format. It's really weird.
        return self.get_cards_values_df()

    def get_cards_values_df(self) -> pd.DataFrame:
        """Gets a dataframe of all cards with values for a user based on all their weighted deck searches."""
        value_dfs = self._get_individual_value_dfs()
        combined_value_dfs = pd.concat(value_dfs)
        summed_value_df = combined_value_dfs.groupby(['set_num', 'card_num', 'count_in_deck']).sum()
        summed_value_df.reset_index(inplace=True)

        return summed_value_df

    def _get_individual_value_dfs(self) -> typing.List[pd.DataFrame]:
        """Get a list of ValueDicts for a user, each based on a single weighted deck search."""
        value_dfs = []
        for weighted_search in self.weighted_deck_searches:
            value_df = weighted_search.get_value_df()
            value_dfs.append(value_df)

        return value_dfs


class GetOverallValueDict:
    """Callable to get a user's value dict (card playsets to values) given their weighted deck searches."""

    def __init__(self, weighted_deck_searches):
        self.weighted_deck_searches = weighted_deck_searches

    def __call__(self):
        return self.get_overall_value_dict()

    def get_overall_value_dict(self) -> card_collections.ValueDict:
        """Gets a ValueDict for a user based on all their weighted deck searches."""
        values = self._init_value_dict()

        value_dicts = self._get_individual_value_dicts()
        for value_dict in value_dicts:
            values.add(value_dict)

        return values

    @staticmethod
    def _init_value_dict() -> card_collections.ValueDict:
        values = card_collections.ValueDict()
        for card in models.card.ALL_CARDS:
            for play_count in range(4):
                values[card.id][play_count] += 0
        return values

    def _get_individual_value_dicts(self) -> typing.List[card_collections.ValueDict]:
        """Get a list of ValueDicts for a user, each based on a single weighted deck search."""
        value_dicts = []
        for weighted_search in self.weighted_deck_searches:
            value_dict = weighted_search.get_value_dict()
            value_dicts.append(value_dict)

        return value_dicts
