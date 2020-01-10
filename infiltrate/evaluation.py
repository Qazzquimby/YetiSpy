"""Gets card values from a user's weighted deck searches"""
import collections
import typing

import numpy as np
import pandas as pd

import models.card
import models.card_set
import models.deck_search
import models.rarity


# import views.card_values.display_filters


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

    def get_purchase_values_df(self) -> models.deck_search.DeckSearchValue_DF:
        """Gets a dataframe of all purchase options with values based on card values."""
        pack_values = self.get_pack_values()
        pack_cost = 1_000
        campaign_values = self.get_campaign_values()
        campaign_cost = 25_000
        campaign_values = {key: campaign_values[key] * 1000 / campaign_cost for key in campaign_values}
        print('debug')

    def get_pack_values(self):
        card_data = self._get_card_data()
        card_data = card_data.drop_duplicates(['set_num', 'card_num'])  # Assume you only find the next copy of a card.
        original_card_data = card_data.copy()

        card_sets = models.card_set.get_sets_from_set_nums(models.card_set.get_main_set_nums())
        values = collections.defaultdict(int)

        for card_set in card_sets:
            for rarity in models.rarity.RARITIES:
                cards_in_pool = card_data[np.logical_and(card_data['set_num'].isin(card_set.set_nums),
                                                         card_data['rarity'] == rarity.name)]
                total_cards_in_pool = original_card_data[
                    np.logical_and(original_card_data['set_num'].isin(card_set.set_nums),
                                   original_card_data['rarity'] == rarity.name)]

                num_total = max(1, len(total_cards_in_pool))
                num_total /= 4  # Because we dropped duplicates, we are only looking at one copy of each card.

                average_value = sum(cards_in_pool['value']) / num_total
                value_for_pool = rarity.num_in_pack * average_value

                values[card_set] += value_for_pool
        return values

    def get_campaign_values(self):
        card_data = self._get_card_data()
        card_sets = models.card_set.get_sets_from_set_nums(models.card_set.get_campaign_set_nums())
        values = collections.defaultdict(int)

        for card_set in card_sets:
            cards_in_pool = card_data[card_data['set_num'].isin(card_set.set_nums)]
            value_for_pool = sum(cards_in_pool['value'])
            values[card_set] += value_for_pool

        return values

    def _get_card_data(self):
        all_cards = models.card.AllCards()
        card_data = self.card_values_df.set_index(['set_num', 'card_num']).join(
            all_cards.df.set_index(['set_num', 'card_num'])).reset_index()

        card_data = views.card_values.display_filters.create_is_owned_column(card_data, self.user)
        card_data = card_data[card_data['is_owned'] == False]

        return card_data


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
