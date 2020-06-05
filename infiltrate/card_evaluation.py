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
import models.card
import models.rarity
import models.user
from models.deck_search import DeckSearchHasCard, WeightedDeckSearch


class _CardCopyColumns(abc.ABC):
    """Holds dataframe of cards with copy #s to attach other information to"""

    SET_NUM = "set_num"
    CARD_NUM = "card_num"
    COUNT_IN_DECK = "count_in_deck"

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __eq__(self, other):
        return type(self) == type(other) and self.df.sort_index(axis=1).equals(
            other.df.sort_index(axis=1)
        )


class _PlayCountColumns(_CardCopyColumns):
    PLAY_COUNT = "num_decks_with_count_or_less"


class PlayCountFrame(_PlayCountColumns):
    """Has column PLAY_COUNT representing the number of decks containing
    the weighted count of that card in decks of all deck searches"""

    @classmethod
    def from_weighted_deck_searches(
        cls,
        weighted_deck_searches: t.List[WeightedDeckSearch],
        card_data: models.card.CardData,
    ):
        """Build the dataframe from the list of weighted deck searches."""
        play_count_dfs: t.List[pd.DataFrame] = []
        for weighted_deck_search in weighted_deck_searches:
            play_count_dfs.append(cls._get_count_df(weighted_deck_search))

        combined_df = cls._sum_count_dfs(play_count_dfs)

        index_keys = [PlayValueFrame.CARD_NUM, PlayValueFrame.SET_NUM]
        added_card_data_df = (
            combined_df.set_index(index_keys)
            .join(card_data.df.set_index(index_keys))
            .reset_index()
        )

        return cls(added_card_data_df)

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
    IS_OWNED = "is_owned"


class PlayValueFrame(_PlayValueColumns):
    """Has column play_value representing how good it is to be able to play that card,
    on a scale of 0-100.
    This is very similar to own value, but doesn't account for reselling."""

    SCALE = 100

    @classmethod
    def from_play_rates(cls, play_rate_frame: PlayRateFrame, ownership: pd.DataFrame):
        """Constructor deriving values from play rates."""
        # todo account for collection fit.
        df = play_rate_frame.df.copy()
        df[cls.PLAY_VALUE] = df[cls.PLAY_COUNT] * cls.SCALE / df[cls.PLAY_COUNT].max()

        df[cls.IS_OWNED] = models.user.owns_card.create_is_owned_series(
            play_rate_frame.df, ownership
        )

        return cls(df)


class _PlayCraftEfficiencyColumns(_PlayValueColumns):
    PLAY_CRAFT_EFFICIENCY = "play_craft_efficiency"
    CRAFT_COST = "craft_cost"


class PlayCraftEfficiencyFrame(_PlayCraftEfficiencyColumns):
    """Has columns craft_cost and play_craft_efficiency representing the card's
    shiftstone cost to craft, and its play value divided by that cost.
    This is very similar to own crafting efficiency, but doesn't account for reselling.
    """

    @classmethod
    def from_play_value(cls, play_value_frame: PlayValueFrame):
        """Constructor for getting play craft efficiency from play value and cost."""
        df: pd.DataFrame = play_value_frame.df.copy()

        df[cls.CRAFT_COST] = df[models.card.CardData.RARITY].apply(
            lambda rarity: models.rarity.rarity_from_name[rarity].enchant
        )

        df[cls.PLAY_CRAFT_EFFICIENCY] = df[cls.PLAY_VALUE] / df[cls.CRAFT_COST]

        return cls(df)


class _OwnValueColumns(_PlayCraftEfficiencyColumns):
    SELL_COST = "sell_cost"
    RESELL_VALUE = "resell_value"
    OWN_VALUE = "own_value"


class OwnValueFrame(_OwnValueColumns):
    """Has columns -sell_cost: the amount of shiftstone from disenchanting,
    -resell_value: the amount of expected value the shiftstone from disenchanting has,
    -own_value: the value of owning a card, including the possibility of reselling it.
    """

    @classmethod
    def from_play_craft_efficiency(
        cls, play_craft_efficiency: PlayCraftEfficiencyFrame, num_options_considered=20
    ):
        """Constructs the own_value """

        df = play_craft_efficiency.df.copy()
        df[cls.SELL_COST] = df[models.card.CardData.RARITY].apply(
            lambda rarity: models.rarity.rarity_from_name[rarity].disenchant
        )

        value_of_shiftstone = cls._value_of_shiftstone(
            play_craft_efficiency, num_options_considered
        )

        df[cls.RESELL_VALUE] = df[cls.SELL_COST] * value_of_shiftstone

        df[cls.OWN_VALUE] = df[[cls.PLAY_VALUE, cls.RESELL_VALUE]].max(axis=1)

        return cls(df)

    @classmethod
    def from_user(cls, user: models.user.User, card_data: models.card.CardData):
        """Creates from a user, performing the entire pipeline."""
        # todo cache this.
        weighted_deck_searches = user.weighted_deck_searches
        play_count = PlayCountFrame.from_weighted_deck_searches(weighted_deck_searches)
        play_rate = PlayRateFrame.from_play_counts(play_count)
        play_value = PlayValueFrame.from_play_rates(play_rate)
        play_craft_efficiency = PlayCraftEfficiencyFrame.from_play_value(
            play_value_frame=play_value, card_data=card_data
        )
        own_value = cls.from_play_craft_efficiency(play_craft_efficiency)
        return own_value

    @classmethod
    def _value_of_shiftstone(
        cls, play_craft_efficiency: PlayCraftEfficiencyFrame, num_options_considered=20
    ):
        """Gets the top num_options crafting efficiencies and averages them to predict
        how much value the user will get from crafting."""
        efficiencies = play_craft_efficiency.df.sort_values(
            play_craft_efficiency.PLAY_CRAFT_EFFICIENCY, ascending=False
        )

        top_efficiencies = efficiencies.head(num_options_considered)
        avg_top_efficiency = (
            sum(top_efficiencies[OwnValueFrame.PLAY_CRAFT_EFFICIENCY])
            / num_options_considered
        )

        return avg_top_efficiency


class _OwnCraftEfficiencyColumns(_OwnValueColumns):
    OWN_CRAFT_EFFICIENCY = "own_craft_efficiency"


class OwnCraftEfficiencyFrame(_OwnCraftEfficiencyColumns):
    """Has column own_craft_efficiency for the value of owning the card divided
    by the shiftstone cost."""

    @classmethod
    def from_own_value(cls, own_value: OwnValueFrame):
        """Constructor deriving efficiency from own values and cost."""
        df: pd.DataFrame = own_value.df.copy()

        df[cls.OWN_CRAFT_EFFICIENCY] = df[cls.OWN_VALUE] / df[cls.CRAFT_COST]

        return cls(df)
