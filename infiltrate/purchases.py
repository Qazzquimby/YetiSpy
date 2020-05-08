"""Handles things that can be bought, such as packs, draft, and league."""
import abc
import collections
import re
import typing as t

import numpy as np
import pandas as pd

import browser
import models.card
import models.card_set
import models.deck_search
import models.rarity
import models.user
import rewards

PurchaseRow = t.Tuple[str, int, float, float]


class PurchaseEvaluator(abc.ABC):
    """ABC for evaluable purchase types"""

    def __init__(self, card_data, cost: int):
        self.card_data = card_data
        self.cost = cost

    def get_values(self) -> dict:
        """Get a list of average values for purchases."""
        raise NotImplementedError

    def get_df_rows(self) -> t.List[t.List]:
        """Gets rows for the purchase dataframe.
        Format is name, cost, value, value/cost"""
        raise NotImplementedError

    def _make_row(self, name, value) -> PurchaseRow:
        row = (name, self.cost, value, 1000 * value / self.cost)
        return row


class PackEvaluator(PurchaseEvaluator):
    """Evaluates all packs"""

    def __init__(self, card_data):
        super().__init__(card_data, cost=1_000)

    def get_values(self) -> dict:
        values = {card_set: card_pack.get_value(self.card_data) for
                  card_set, card_pack in rewards.CARD_PACKS.items()}
        return values

    def get_df_rows(self) -> t.List[PurchaseRow]:
        pack_values = self.get_values()

        rows = []
        for card_set in pack_values.keys():
            name = models.card_set._get_set_name(card_set.set_nums[0])
            rows.append(self._make_row(name, pack_values[card_set]))
        return rows


class CampaignEvaluator(PurchaseEvaluator):
    """Evaluates all campaigns"""

    def __init__(self, card_data):
        super().__init__(card_data, cost=25_000)

    def get_values(self):
        card_data = self.card_data.copy()
        card_sets = models.card_set.get_campaign_sets()
        values = collections.defaultdict(int)

        for card_set in card_sets:
            cards_in_pool = card_data[
                np.logical_and(
                    card_data['set_num'].isin(card_set.set_nums),
                    card_data['is_owned'] == False)
            ]
            value_for_pool = sum(cards_in_pool['value'])
            values[card_set] += value_for_pool

        return values

    def get_df_rows(self) -> t.List[PurchaseRow]:
        campaign_values = self.get_values()

        rows = []
        for card_set in campaign_values.keys():
            name = models.card_set._get_set_name(card_set.set_nums[0])
            rows.append(self._make_row(name, campaign_values[card_set]))
        return rows


class DraftEvaluator(PurchaseEvaluator, abc.ABC):
    """ABC for evaluating drafts."""

    def __init__(self, card_data):
        super().__init__(card_data, cost=5_000)

    def _get_packs_value(self):
        newest_set = models.card_set.get_newest_main_set()
        newest_pack_value = rewards.CARD_PACKS[newest_set].get_value(
            self.card_data)
        draft_pack_value = rewards.DRAFT_PACK.get_value(self.card_data)
        value = 2 * newest_pack_value + 2 * draft_pack_value
        return value


class LoseAllGamesDraftEvaluator(DraftEvaluator):

    def get_values(self) -> float:
        return self._get_packs_value()

    def get_df_rows(self) -> t.List[PurchaseRow]:
        draft_value = self.get_values()
        return [self._make_row('Lose All Games Draft', draft_value)]


class AverageDraftEvaluator(DraftEvaluator):
    """Evaluates a single where the player has an average win rate."""

    def get_values(self) -> float:
        packs_value = self._get_packs_value()

        average_wins_value = self._get_average_wins_value()

        value = packs_value + average_wins_value
        return value

    def _get_average_wins_value(self) -> float:
        average_win_value = 0
        for chance, win_rewards in self._get_win_chances_and_rewards():
            win_value = sum([reward.get_value(self.card_data)
                             for reward in win_rewards])

            average_win_value += win_value * chance
        return average_win_value

    def _get_win_chances_and_rewards(
            self) -> t.Iterator[t.Tuple[float, t.List[rewards.Reward]]]:
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
                             2 * [rewards.SILVER_CHEST]
                             + 1 * [rewards.GOLD_CHEST],
                             1 * [rewards.SILVER_CHEST]
                             + 2 * [rewards.GOLD_CHEST],
                             3 * [rewards.GOLD_CHEST],
                             2 * [rewards.GOLD_CHEST]
                             + 1 * [rewards.DIAMOND_CHEST],
                             1 * [rewards.GOLD_CHEST]
                             + 2 * [rewards.DIAMOND_CHEST],
                             3 * [rewards.DIAMOND_CHEST], ]
        return zip(chances_of_n_wins, rewards_of_n_wins)

    def get_df_rows(self) -> t.List[PurchaseRow]:
        draft_value = self.get_values()
        return [self._make_row('Average Draft', draft_value)]


class LeagueEvaluator(PurchaseEvaluator, abc.ABC):
    """ABC for league purchases."""

    def __init__(self, card_data):
        super().__init__(card_data, cost=12_500)

    def get_league_packs_value(self) -> float:
        pack_counts = get_league_packs()

        pack_values = PackEvaluator(self.card_data).get_values()

        total_value = 0
        for pack in pack_counts.keys():
            count = pack_counts[pack]
            value_per_pack = pack_values[pack]
            total_value += count * value_per_pack

        return total_value


class FirstLeagueEvaluator(LeagueEvaluator):
    """Evaluates the first league of a given month."""

    def get_value(self):
        packs_value = self.get_league_packs_value()

        # Win rewards
        """
#wins      chance      Ranks
34+        4.4e-06      1-10	    20x Card Packs	1x Random Premium Legendary
33?        1.95e-05     11-50	    17x Card Packs	1x Random Premium Legendary
32?        7.08e-05     51-100	    15x Card Packs	1x Random Premium Legendary
30-31      0.0010323    101-500	    13x Card Packs	1x Random Premium Legendary
25-29      0.0758747    501-1000	12x Card Packs	1x Random Premium Rare
21-24      0.3602328    1001-2500	9x Card Packs	1x Random Premium Rare
else       0.5627655    2501-5000	8x Card Packs	1x Random Premium Rare
                    5001-10000	7x Card Packs	1x Random Premium Uncommon
                    10001+	    4x Card Packs	1x Random Premium Uncommon

Top 1000 has been at 21 wins, top 500 at 25 wins and top 100 at 30 wins

        5 - 8e-07
        6 - 4.4e-06
        7 - 1.71e-05
        8 - 6.95e-05
        9 - 0.0002489
        10 - 0.0007704
        11 - 0.0021132
        12 - 0.0050997
        13 - 0.0109689
        14 - 0.0211449
        15 - 0.0365552
        16 - 0.0571812
        17 - 0.0807354
        18 - 0.1030886
        19 - 0.1193797
        20 - 0.1253876
        21 - 0.1192975
        22 - 0.1030655
        23 - 0.08071
        24 - 0.0571598
        25 - 0.0366103
        26 - 0.02112
        27 - 0.0109266
        28 - 0.0050883
        29 - 0.0021295
        30 - 0.000784
        31 - 0.0002483
        32 - 7.08e-05
        33 - 1.95e-05
        34 - 3.6e-06
        35 - 6e-07
        36 - 2e-07
        """

        average_win_value = 0
        chances_of_rank = [4.4e-06,
                           1.95e-05,
                           7.08e-05,
                           0.0010323,
                           0.0758747,
                           0.3602328,
                           0.5627655, ]

        rewards_of_rank = [
            20 * [rewards.Reward(
                card_classes=rewards.get_pack_contents_for_sets(
                    [models.card_set.get_newest_main_set()]
                ))]
            + [rewards.Reward(card_classes=[
                rewards.CardClass(rarity=models.rarity.LEGENDARY,
                                  is_premium=True)])],
            17 * [rewards.Reward(
                card_classes=rewards.get_pack_contents_for_sets(
                    [models.card_set.get_newest_main_set()]
                ))]
            + [rewards.Reward(card_classes=[
                rewards.CardClass(rarity=models.rarity.LEGENDARY,
                                  is_premium=True)])],
            15 * [rewards.Reward(
                card_classes=rewards.get_pack_contents_for_sets(
                    [models.card_set.get_newest_main_set()]
                ))]
            + [rewards.Reward(card_classes=[
                rewards.CardClass(rarity=models.rarity.LEGENDARY,
                                  is_premium=True)])],
            13 * [rewards.Reward(
                card_classes=rewards.get_pack_contents_for_sets(
                    [models.card_set.get_newest_main_set()]
                ))]
            + [rewards.Reward(card_classes=[
                rewards.CardClass(rarity=models.rarity.LEGENDARY,
                                  is_premium=True)])],
            12 * [rewards.Reward(
                card_classes=rewards.get_pack_contents_for_sets(
                    [models.card_set.get_newest_main_set()]
                ))]
            + [rewards.Reward(card_classes=[
                rewards.CardClass(rarity=models.rarity.RARE,
                                  is_premium=True)])],
            9 * [rewards.Reward(
                card_classes=rewards.get_pack_contents_for_sets(
                    [models.card_set.get_newest_main_set()]
                ))]
            + [rewards.Reward(card_classes=[
                rewards.CardClass(rarity=models.rarity.RARE,
                                  is_premium=True)])],
            8 * [rewards.Reward(
                card_classes=rewards.get_pack_contents_for_sets(
                    [models.card_set.get_newest_main_set()]
                ))]
            + [rewards.Reward(card_classes=[
                rewards.CardClass(rarity=models.rarity.RARE,
                                  is_premium=True)])],

        ]

        for win_num in range(len(rewards_of_rank)):
            chance = chances_of_rank[win_num]
            win_rewards = rewards_of_rank[win_num]
            win_value = 0
            for reward in win_rewards:
                reward_value = reward.get_value(self.card_data)
                win_value += reward_value
            weighted_win_value = chance * win_value
            average_win_value += weighted_win_value

        value = packs_value + average_win_value
        return value

    def get_df_rows(self):
        first_league_value = self.get_value()
        return [self._make_row('First_League', first_league_value)]


class AdditionalLeagueEvaluator(LeagueEvaluator):
    """Evaluates any league in a month after the first."""

    def get_value(self):
        return self.get_league_packs_value()

    def get_df_rows(self):
        additional_league_value = self.get_value()
        return [self._make_row('Additional_League', additional_league_value)]


def get_league_packs() -> t.Dict[models.card_set.CardSet, int]:
    url = 'https://eternalcardgame.fandom.com/wiki/Leagues'
    xpath = '//*[@id="mw-content-text"]/table[3]/tbody/tr[last()]'
    full_text = browser.get_str_from_url_and_xpath(url, xpath)
    full_text = full_text.replace('\n', ' ')
    pack_texts = re.findall(r'\dx\s\D+', full_text)
    set_name_counter = collections.defaultdict(int)

    for pack_text in pack_texts:
        num_packs = int(pack_text.split('x ')[0])
        set_name = pack_text.split('x ')[1].strip()
        set_name_counter[set_name] += num_packs

    card_set_counter = {
        models.card_set.get_set_from_name(set_name): set_name_counter[set_name]
        for set_name in set_name_counter.keys()}

    return card_set_counter


class _PurchasesValueDataframeGetter:
    """Helper class used by get_purchase_values_df."""

    def __init__(self, card_values_df: models.deck_search.DeckSearchValue_DF,
                 user):
        self.card_values_df = card_values_df
        self.user = user

        self.card_data: t.Final = self._get_card_data()

        self.purchase_evaluators = [
            PackEvaluator(self.card_data),
            CampaignEvaluator(self.card_data),
            AverageDraftEvaluator(self.card_data),
            LoseAllGamesDraftEvaluator(self.card_data),
            FirstLeagueEvaluator(self.card_data),
            AdditionalLeagueEvaluator(self.card_data)
        ]

    def get_purchase_values_df(self) -> models.deck_search.DeckSearchValue_DF:
        """Gets a dataframe of all purchase options
        with values based on card values."""
        columns = ['name', 'gold_cost', 'value', 'value_per_gold']
        df_constructor = []
        for purchase_evaluator in self.purchase_evaluators:
            df_constructor += purchase_evaluator.get_df_rows()

        values_df = pd.DataFrame(df_constructor, columns=columns)
        return values_df

    def _get_card_data(self):
        all_cards = models.card.AllCards()
        card_data = self.card_values_df.set_index(
            ['set_num', 'card_num']).join(
            all_cards.df.set_index(['set_num', 'card_num'])).reset_index()

        card_data = models.user.user_owns_card.create_is_owned_column(
            card_data, self.user)

        return card_data
