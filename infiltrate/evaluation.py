"""Gets card values from a user's weighted deck searches"""
import collections
import typing

import numpy as np
import pandas as pd

import models.card
import models.card_set
import models.deck_search
import models.rarity
import rewards


class _CardValueDataframeGetter:
    """Helper class used by get_cards_values_df."""

    def __init__(self, weighted_deck_searches: typing.List[models.deck_search.WeightedDeckSearch]):
        self.weighted_deck_searches = weighted_deck_searches

    def get_cards_values_df(self) -> models.deck_search.DeckSearchValue_DF:
        """Gets a dataframe of all cards with values for a user based on all their weighted deck searches."""
        value_dfs = [weighted_search.get_value_df() for weighted_search in self.weighted_deck_searches]
        summed_value_df = self._merge_value_dfs(value_dfs)
        normalized_value_df = self._normalize_value_df(summed_value_df)
        return normalized_value_df

    @staticmethod
    def _merge_value_dfs(value_dfs: typing.List[models.deck_search.DeckSearchValue_DF]) \
            -> models.deck_search.DeckSearchValue_DF:
        combined_value_dfs = pd.concat(value_dfs)
        summed_value_df = combined_value_dfs.groupby(['set_num', 'card_num', 'count_in_deck']).sum()
        # Todo I think this is also summing the deck search id?
        summed_value_df.reset_index(inplace=True)
        return summed_value_df

    @staticmethod
    def _normalize_value_df(value_df: models.deck_search.DeckSearchValue_DF) -> models.deck_search.DeckSearchValue_DF:
        normalized = value_df.copy()
        normalized['value'] = value_df['value'] * 100 / max(1, max(value_df['value']))
        return normalized


def get_cards_values_df(weighted_deck_searches: typing.List[models.deck_search.WeightedDeckSearch]) \
        -> models.deck_search.DeckSearchValue_DF:
    getter = _CardValueDataframeGetter(weighted_deck_searches)
    df = getter.get_cards_values_df()
    return df


class _PurchasesValueDataframeGetter:
    """Helper class used by get_purchase_values_df."""

    def __init__(self, card_values_df: models.deck_search.DeckSearchValue_DF, user):
        self.card_values_df = card_values_df
        self.user = user

        self.card_data: typing.Final = self._get_card_data()

    def get_purchase_values_df(self) -> models.deck_search.DeckSearchValue_DF:
        """Gets a dataframe of all purchase options with values based on card values."""
        pack_values = self.get_pack_values()
        pack_cost = 1_000
        campaign_values = self.get_campaign_values()
        campaign_cost = 25_000
        campaign_values = {key: campaign_values[key] * 1000 / campaign_cost for key in campaign_values}

        draft_values = self.get_draft_values()
        draft_cost = 5_000
        print('debug')

    def get_pack_values(self):
        card_data = self.card_data.copy()
        card_data = card_data.drop_duplicates(['set_num', 'card_num'])  # Assume you only find the next copy of a card.

        card_sets = models.card_set.get_sets_from_set_nums(models.card_set.get_main_set_nums())
        values = collections.defaultdict(int)

        for card_set in card_sets:
            for rarity in models.rarity.RARITIES:
                cards_in_pool = card_data[np.logical_and(card_data['set_num'].isin(card_set.set_nums),
                                                         card_data['rarity'] == rarity.name)]

                num_total = max(1, len(cards_in_pool))
                num_total /= 4  # Because we dropped duplicates, we are only looking at one copy of each card.

                average_value = sum(cards_in_pool['value']) / num_total
                value_for_pool = rarity.num_in_pack * average_value

                values[card_set] += value_for_pool
        return values

    def get_campaign_values(self):
        card_data = self.card_data.copy()
        card_sets = models.card_set.get_sets_from_set_nums(models.card_set.get_campaign_set_nums())
        values = collections.defaultdict(int)

        for card_set in card_sets:
            cards_in_pool = card_data[card_data['set_num'].isin(card_set.set_nums)]
            value_for_pool = sum(cards_in_pool['value'])
            values[card_set] += value_for_pool

        return values

    def get_draft_values(self):
        card_data = self.card_data.copy()
        card_data = card_data.drop_duplicates(['set_num', 'card_num'])  # Assume you only find the next copy of a card.

        # Newest set
        newest_pack_value = 0
        newest_set = models.card_set.get_sets_from_set_nums([models.card_set.get_newest_main_set_num()])[0]
        for rarity in models.rarity.RARITIES:
            cards_in_pool = card_data[np.logical_and(card_data['set_num'].isin(newest_set.set_nums),
                                                     card_data['rarity'] == rarity.name)]

            num_total = max(1, len(cards_in_pool))
            num_total /= 4  # Because we dropped duplicates, we are only looking at one copy of each card.

            average_value = sum(cards_in_pool['value']) / num_total
            value_for_pool = rarity.num_in_pack * average_value

            newest_pack_value += 2 * value_for_pool

        # Draft pack
        draft_pack_value = 0
        for rarity in models.rarity.RARITIES:  # todo generalize and combine with the above loop.
            cards_in_pool = card_data[np.logical_and(card_data['is_in_draft_pack'] == True,
                                                     card_data['rarity'] == rarity.name)]

            num_total = max(1, len(cards_in_pool))
            num_total /= 4  # Because we dropped duplicates, we are only looking at one copy of each card.

            average_value = sum(cards_in_pool['value']) / num_total
            value_for_pool = rarity.num_in_pack * average_value

            draft_pack_value += 2 * value_for_pool

        # Win rewards
        """
        0 - 0.1249783 - 2 Silver Chests
        1 - 0.1875412 - 3 Silver Chests
        2 - 0.1874744 - 2 Silver Chests	+	1 Gold Chest
        3 - 0.1562196 - 1 Silver Chests	+	2 Gold Chests
        4 - 0.1171667 - 3 Gold Chests
        5 - 0.0821073 - 2 Gold Chests	+	1 Diamond Chest
        6 - 0.0547650 - 1 Gold Chests	+	2 Diamond Chests
        7 - 0.0897475 - 3 Diamond Chests
        """
        wins_value = 0
        chances_of_n_wins = [0.1249783,
                             0.1875412,
                             0.1874744,
                             0.1562196,
                             0.1171667,
                             0.0821073,
                             0.0547650,
                             0.0897475, ]

        rewards_of_n_wins = [2 * [rewards.SILVER_CHEST],
                             3 * [rewards.SILVER_CHEST],
                             2 * [rewards.SILVER_CHEST] + 1 * [rewards.GOLD_CHEST],
                             1 * [rewards.SILVER_CHEST] + 2 * [rewards.GOLD_CHEST],
                             3 * [rewards.GOLD_CHEST],
                             2 * [rewards.GOLD_CHEST] + 1 * [rewards.DIAMOND_CHEST],
                             1 * [rewards.GOLD_CHEST] + 2 * [rewards.DIAMOND_CHEST],
                             3 * [rewards.DIAMOND_CHEST], ]

        for win_num in range(8):
            chance = chances_of_n_wins[win_num]
            win_rewards = rewards_of_n_wins[win_num]
            win_value = 0
            for reward in win_rewards:
                reward_value = get_value_of_reward(reward, card_data)
                win_value += reward_value
            win_value = chance * win_value
            wins_value += win_value

        value = newest_pack_value + draft_pack_value + wins_value
        return value

    def _get_card_data(self):
        all_cards = models.card.AllCards()
        card_data = self.card_values_df.set_index(['set_num', 'card_num']).join(
            all_cards.df.set_index(['set_num', 'card_num'])).reset_index()

        card_data = models.user.user_owns_card.create_is_owned_column(card_data, self.user)
        # todo move create_is_owned to a utility file like ownership

        card_data = card_data[card_data['is_owned'] == False]

        return card_data


def get_value_of_reward(reward: rewards.Reward, card_data) -> float:
    total_value = 0
    # todo get value of gold and shiftstone

    for card_class_with_amount in reward.card_classes_with_amounts:
        card_class_with_amount: rewards.CardClassWithAmount
        card_data = card_data.drop_duplicates(['set_num', 'card_num'])  # Assume you only find the next copy of a card.

        value_for_sets = collections.defaultdict(int)
        for card_set in card_class_with_amount.card_class.sets:
            for rarity in card_class_with_amount.card_class.rarities:
                cards_in_pool = card_data[np.logical_and(card_data['set_num'].isin(card_set.set_nums),
                                                         card_data['rarity'] == rarity.name)]

                num_total = max(1, len(cards_in_pool))
                num_total /= 4  # Because we dropped duplicates, we are only looking at one copy of each card.

                average_value = sum(cards_in_pool['value']) / num_total
                value_for_pool = rarity.num_in_pack * average_value

                value_for_sets[card_set] += value_for_pool

        value_for_card_class = sum(value_for_sets.values()) / len(value_for_sets.keys())
        value_for_card_class *= card_class_with_amount.amount

        total_value += value_for_card_class

    return total_value


def get_purchases_values_df(card_values_df: models.deck_search.DeckSearchValue_DF, user):
    getter = _PurchasesValueDataframeGetter(card_values_df, user)
    df = getter.get_purchase_values_df()
    return df


if __name__ == '__main__':
    import sqlalchemy.orm.session
    import infiltrate
    import models.user

    weighted_deck_searches = models.deck_search.get_default_weighted_deck_searches(-1)
    [sqlalchemy.orm.session.make_transient_to_detached(s) for s in weighted_deck_searches]
    [infiltrate.db.session.add(s) for s in weighted_deck_searches]

    card_values = get_cards_values_df(weighted_deck_searches)
    user = models.user.get_by_id(22)

    purchase_values = get_purchases_values_df(card_values, user=user)

    print('debug')
