"""Gets card values from a user's weighted deck searches"""
import typing as t

import pandas as pd

import models.deck_search
import models.rarity


def get_cards_values_df(
    weighted_deck_searches: t.List[models.deck_search.WeightedDeckSearch],
) -> models.deck_search.DeckSearchValue_DF:
    """Gets a dataframe of all cards with values for a user
    based on all their weighted deck searches."""
    getter = _CardValueDataframeGetter(weighted_deck_searches)
    return getter.get_cards_values_df()


class _CardValueDataframeGetter:
    """Helper class used by get_cards_values_df."""

    def __init__(
        self, weighted_deck_searches: t.List[models.deck_search.WeightedDeckSearch]
    ):
        self.weighted_deck_searches = weighted_deck_searches

    def get_cards_values_df(self) -> models.deck_search.DeckSearchValue_DF:
        """Gets a dataframe of all cards with values for a user
        based on all their weighted deck searches."""
        value_dfs = [
            weighted_search.get_value_df()
            for weighted_search in self.weighted_deck_searches
        ]
        summed_value_df = self._merge_value_dfs(value_dfs)
        normalized_value_df = self._normalize_value_df(summed_value_df)
        return normalized_value_df

    @staticmethod
    def _merge_value_dfs(
        value_dfs: t.List[models.deck_search.DeckSearchValue_DF],
    ) -> models.deck_search.DeckSearchValue_DF:
        combined_value_dfs = pd.concat(value_dfs)
        summed_value_df = combined_value_dfs.groupby(
            ["set_num", "card_num", "count_in_deck"]
        ).sum()
        # Todo I think this is also summing the deck search id?
        summed_value_df.reset_index(inplace=True)
        return summed_value_df

    @staticmethod
    def _normalize_value_df(
        value_df: models.deck_search.DeckSearchValue_DF,
    ) -> models.deck_search.DeckSearchValue_DF:
        normalized = value_df.copy()
        normalized["value"] = value_df["value"] * 100 / max(1, max(value_df["value"]))
        return normalized


if __name__ == "__main__":
    import sqlalchemy.orm.session
    import infiltrate
    import models.user

    weighted_deck_searches = models.deck_search.get_default_weighted_deck_searches(-1)

    [
        sqlalchemy.orm.session.make_transient_to_detached(s)
        for s in weighted_deck_searches
    ]

    [infiltrate.db.session.add(s) for s in weighted_deck_searches]

    card_values = get_cards_values_df(weighted_deck_searches)
    user = models.user.get_by_id(22)
    from purchases import get_purchase_values

    purchase_values = get_purchase_values(card_values, user)

    print("debug")
