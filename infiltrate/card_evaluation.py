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

import werkzeug.local

import infiltrate.df_types as df_types
import infiltrate.models.deck_constants as deck_constants
from infiltrate.models.rarity import Rarity
from infiltrate.models.user import User, collection
import infiltrate.models.card_set as card_set
import infiltrate.rewards as rewards
import infiltrate.card_frame_bases as card_frame_bases
from infiltrate.models.deck_search import WeightedDeckSearch, get_weighted_deck_searches


# TODO Important. Add card values to the database as a column on cards. Everyone has the
#   same basic card values. Later mask with ownership to make individual.


class PlayCountFrame(card_frame_bases.CardCopy):
    """Has column play_count representing the number of decks containing
     the weighted count of that card in decks of all deck searches"""

    PLAY_COUNT_NAME = "num_decks_with_count_or_less"

    RARITY_NAME = "rarity"
    IMAGE_URL_NAME = "image_url"
    DETAILS_URL_NAME = "details_url"
    IS_IN_DRAFT_PACK_NAME = "is_in_draft_pack"

    def __init__(self, *args):
        card_frame_bases.CardCopy.__init__(self, *args)
        self.num_decks_with_count_or_less = self.num_decks_with_count_or_less

    @classmethod
    def from_weighted_deck_searches(
        cls,
        weighted_deck_searches: t.List[WeightedDeckSearch],
        card_details: card_frame_bases.CardDetails,
    ):
        """Build the dataframe from the list of weighted deck searches."""
        play_count_dfs: t.List[pd.DataFrame] = []
        for weighted_deck_search in weighted_deck_searches:
            play_count_dfs.append(cls._get_count_df(weighted_deck_search))

        index_keys = [cls.SET_NUM_NAME, cls.CARD_NUM_NAME]
        combined_df = cls._sum_count_dfs(play_count_dfs).set_index(index_keys)

        added_card_data_df = combined_df.join(card_details)

        return cls(added_card_data_df)

    @classmethod
    def _get_count_df(cls, weighted_deck_search: WeightedDeckSearch):
        """Get a dataframe representing the number of times a card is seen in
        decks in the deck search, times its weight."""
        play_count_df = df_types.sqlalchemy_objects_to_df(
            weighted_deck_search.deck_search.cards
        )
        play_count_df.num_decks_with_count_or_less *= weighted_deck_search.weight
        return play_count_df

    @classmethod
    def _sum_count_dfs(cls, play_count_dfs: t.List[pd.DataFrame]) -> pd.DataFrame:
        combined = pd.concat(play_count_dfs).copy()
        summed = (
            combined.groupby(
                [combined.set_num, combined.card_num, combined.count_in_deck]
            )
            .sum()
            .reset_index()
        )
        return summed


class PlayRateFrame(PlayCountFrame):
    """Has column play_rate representing the fraction of decks containing the card
 in relevant deck searches."""

    PLAY_RATE_NAME = "play_rate"

    def __init__(self, *args):
        PlayCountFrame.__init__(self, *args)
        self.play_rate = self.play_rate

    @classmethod
    def from_play_counts(cls, play_count_frame: PlayCountFrame):
        """Constructor deriving play rates from play counts"""
        df = play_count_frame.copy()
        total_card_inclusions = sum(df[cls.PLAY_COUNT_NAME])
        df[cls.PLAY_RATE_NAME] = (
            df[cls.PLAY_COUNT_NAME]
            * deck_constants.AVG_COLLECTABLE_CARDS_IN_DECK
            / total_card_inclusions
        )
        return cls(df)


class PlayValueFrame(PlayRateFrame):
    """Has column play_value representing how good it is to be able to play that card,
    on a scale of 0-100.
    This is very similar to own value, but doesn't account for reselling."""

    VALUE_SCALE = 100

    PLAY_VALUE_NAME = "play_value"
    IS_OWNED_NAME = "is_owned"
    _metadata = ["user"]

    def __init__(self, user: User, *args):
        PlayRateFrame.__init__(self, *args)
        self.user = user
        self.play_value = self.play_value

    def __hash__(self):
        return hash(self.user)

    @classmethod
    def from_play_rates(
        cls, user: User, play_rate_frame: PlayRateFrame, ownership: pd.DataFrame,
    ):
        """Constructor deriving values from play rates."""
        # todo account for collection fit.
        df: pd.DataFrame = play_rate_frame.copy()
        df[cls.PLAY_VALUE_NAME] = (
            df["num_decks_with_count_or_less"]
            * cls.VALUE_SCALE
            / df["num_decks_with_count_or_less"].max()
        )

        ownership_frame = collection.create_is_owned_series(play_rate_frame, ownership)

        df = df.join(
            ownership_frame.drop(
                [cls.SET_NUM_NAME, cls.CARD_NUM_NAME, cls.COUNT_IN_DECK_NAME], axis=1
            )
        )

        return cls(user, df)


class PlayCraftEfficiencyFrame(PlayValueFrame):
    """Has columns craft_cost and play_craft_efficiency representing the card's
    shiftstone cost to craft, and its play value divided by that cost.
    This is very similar to own crafting efficiency, but doesn't account for reselling.
    """

    PLAY_CRAFT_EFFICIENCY_NAME = "play_craft_efficiency"
    CRAFT_COST_NAME = "craft_cost"
    FINDABILITY_NAME = "findability"

    def __init__(self, user: User, *args):
        PlayValueFrame.__init__(self, user, *args)

        self.play_craft_efficiency = self.play_craft_efficiency

    @classmethod
    def from_play_value(cls, play_value_frame: PlayValueFrame):
        """Constructor for getting play craft efficiency from play value and cost."""
        df: pd.DataFrame = play_value_frame.copy()

        df[cls.CRAFT_COST_NAME] = df[cls.RARITY_NAME].apply(
            lambda rarity: rarity.enchant
        )

        df[cls.FINDABILITY_NAME] = cls.get_findability(
            rarity=df[cls.RARITY_NAME], set_num=df[cls.SET_NUM_NAME]
        )

        df[cls.PLAY_CRAFT_EFFICIENCY_NAME] = cls.findability_scalar(
            findability=df[cls.FINDABILITY_NAME],
            craft_efficiency=df[cls.PLAY_VALUE_NAME] / df[cls.CRAFT_COST_NAME],
        )

        return cls(play_value_frame.user, df)

    @staticmethod
    @pd.np.vectorize
    def get_findability(rarity: Rarity, set_num: int):
        """Get the chance that a player will find the given card."""
        # todo cost could be calculated once per card rather than once per count
        # TODO allow custom player profiles to override this.
        player: rewards.PlayerRewards = rewards.DEFAULT_PLAYER_REWARD_RATE
        findability = player.get_chance_of_specific_card_drop_in_a_week(
            rarity=rarity, card_set=card_set.CardSet(set_num)
        )
        return findability

    @staticmethod
    @pd.np.vectorize
    def findability_scalar(craft_efficiency: float, findability: float):
        """Scales the craft efficiency based on the findability."""
        return (1 - findability) * craft_efficiency


class OwnValueFrame(PlayCraftEfficiencyFrame):
    """Has columns
    -sell_cost: the amount of shiftstone from disenchanting,
    -resell_value: the amount of expected value the shiftstone from disenchanting has,
    -own_value: the value of owning a card, including the possibility of reselling it.
    """

    SELL_COST_NAME = "sell_cost"
    RESELL_VALUE_NAME = "resell_value"
    OWN_VALUE_NAME = "own_value"

    def __init__(self, user: User, *args):
        if not (isinstance(user, User) or isinstance(user, werkzeug.local.LocalProxy)):
            raise ValueError("Must be given user parameter of type User")

        PlayCraftEfficiencyFrame.__init__(self, user, *args)

        self.sell_cost = self.sell_cost
        self.resell_value = self.resell_value
        self.own_value = self.own_value

    @classmethod
    def from_play_craft_efficiency(
        cls, play_craft_efficiency: PlayCraftEfficiencyFrame, num_options_considered=20
    ):
        """Constructs the own_value """

        df = play_craft_efficiency.copy()
        df[cls.SELL_COST_NAME] = df[cls.RARITY_NAME].apply(
            lambda rarity: rarity.disenchant
        )

        value_of_shiftstone = cls._value_of_shiftstone(
            play_craft_efficiency, num_options_considered
        )

        df[cls.RESELL_VALUE_NAME] = df[cls.SELL_COST_NAME] * value_of_shiftstone

        df[cls.OWN_VALUE_NAME] = df[[cls.PLAY_VALUE_NAME, cls.RESELL_VALUE_NAME]].max(
            axis=1
        )

        return cls(play_craft_efficiency.user, df)

    @classmethod
    def from_user(cls, user: User, card_details: card_frame_bases.CardDetails):
        """Creates from a user, performing the entire pipeline."""
        weighted_deck_searches = get_weighted_deck_searches()
        play_count = PlayCountFrame.from_weighted_deck_searches(
            weighted_deck_searches=weighted_deck_searches, card_details=card_details
        )

        play_rate = PlayRateFrame.from_play_counts(play_count)

        ownership = collection.dataframe_for_user(user)
        play_value = PlayValueFrame.from_play_rates(
            user=user, play_rate_frame=play_rate, ownership=ownership
        )
        play_craft_efficiency = PlayCraftEfficiencyFrame.from_play_value(play_value)
        own_value = cls.from_play_craft_efficiency(play_craft_efficiency)
        return own_value

    @classmethod
    def _value_of_shiftstone(
        cls, play_craft_efficiency: PlayCraftEfficiencyFrame, num_options_considered=20
    ):
        """Gets the top num_options crafting efficiencies and averages them to predict
        how much value the user will get from crafting."""
        efficiencies = play_craft_efficiency.query(
            f"{cls.IS_OWNED_NAME} == False"
        ).sort_values(cls.PLAY_CRAFT_EFFICIENCY_NAME, ascending=False)

        top_efficiencies = efficiencies.head(num_options_considered)
        avg_top_efficiency = (
            sum(top_efficiencies[cls.PLAY_CRAFT_EFFICIENCY_NAME])
            / num_options_considered
        )

        return avg_top_efficiency
