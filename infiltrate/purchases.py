"""Handles things that can be bought, such as packs, draft, and league."""
import abc
import collections
import logging
import typing as t

import pandas as pd

import infiltrate.card_evaluation as card_evaluation
import infiltrate.dwd_news as dwd_news
import infiltrate.models.card.draft as card_draft
import infiltrate.models.card_set as models_card_set
import infiltrate.models.rarity as rarity
import infiltrate.rewards as rewards
from infiltrate.models.user import User

PurchaseRow = t.Tuple[str, str, str, int, float, float]


class PurchaseEvaluator(abc.ABC):
    """ABC for evaluable purchase types"""

    def __init__(self, card_data, cost: int, purchase_type: str):
        self.card_data = card_data
        self.cost = cost
        self.type = purchase_type

    def get_values(self) -> dict:
        """Get a list of average values for purchases."""
        raise NotImplementedError

    def get_df_rows(self) -> t.List[t.List]:
        """Gets rows for the purchase dataframe.
        Format is name, cost, value, value/cost"""
        raise NotImplementedError

    def _make_row(self, name, info_link, value) -> PurchaseRow:
        row = (self.type, name, info_link, self.cost, value, 1000 * value / self.cost)
        return row


class PackEvaluator(PurchaseEvaluator):
    """Evaluates all packs"""

    def __init__(self, card_data):
        super().__init__(card_data, cost=1_000, purchase_type="Card Pack")

    def get_values(self) -> t.Dict[models_card_set.CardSet, int]:
        values = {
            card_set: card_pack.get_value(self.card_data)
            for card_set, card_pack in rewards.CARD_PACKS.items()
        }
        logging.info(f"Pack values: {values}")
        return values

    def get_df_rows(self) -> t.List[PurchaseRow]:
        pack_values = self.get_values()

        rows = [
            self._make_row(
                name=card_set.name,
                info_link=self._make_info_link(card_set),
                value=pack_values[card_set],
            )
            for card_set in pack_values.keys()
        ]
        return rows

    def _make_info_link(self, card_set: models_card_set.CardSet) -> str:
        return f"https://eternalwarcry.com/cards?CardSet={card_set.set_num}"


class CampaignEvaluator(PurchaseEvaluator):
    """Evaluates all campaigns"""

    def __init__(self, card_data):
        super().__init__(card_data, cost=25_000, purchase_type="Campaign")

    def get_values(self):
        card_data = self.card_data.copy()
        card_sets = models_card_set.get_campaign_sets()
        values = collections.defaultdict(int)

        for card_set in card_sets:
            cards_in_pool = card_data.query(
                "set_num == @card_set.set_num and is_owned == False"
            )

            value_for_pool = sum(cards_in_pool["play_value"])
            values[card_set] += value_for_pool
        logging.info(f"Campaign values: {values}")
        return values

    def get_df_rows(self) -> t.List[PurchaseRow]:
        campaign_values = self.get_values()

        rows = []
        for card_set in campaign_values.keys():
            rows.append(
                self._make_row(
                    card_set.name,
                    self._make_info_link(card_set),
                    campaign_values[card_set],
                )
            )
        return rows

    def _make_info_link(self, card_set: models_card_set.CardSet) -> str:
        return f"https://eternalwarcry.com/cards?CardSet={card_set.set_num}"


class DraftEvaluator(PurchaseEvaluator, abc.ABC):
    """ABC for evaluating drafts."""

    BASE_COST = 5_000

    def __init__(self, card_data, expected_gold_earned: float):
        super().__init__(
            card_data,
            cost=int(self.BASE_COST - expected_gold_earned),
            purchase_type="Draft",
        )

    def _get_packs_value(self):
        newest_set = models_card_set.get_newest_main_set()
        newest_pack_value = rewards.CARD_PACKS[newest_set].get_value(self.card_data)
        draft_pack_value = rewards.DRAFT_PACK.get_value(self.card_data)
        value = 2 * newest_pack_value + 2 * draft_pack_value
        return value

    def _get_win_chances_and_rewards(
        self,
    ) -> t.Iterator[t.Tuple[float, t.List[rewards.Reward]]]:
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

        chances_of_n_wins = [
            0.1249783,
            0.1875412,
            0.1874744,
            0.1562196,
            0.1171667,
            0.0821073,
            0.0547650,
            0.0897475,
        ]

        rewards_of_n_wins = [
            2 * [rewards.SILVER_CHEST],
            3 * [rewards.SILVER_CHEST],
            2 * [rewards.SILVER_CHEST] + 1 * [rewards.GOLD_CHEST],
            1 * [rewards.SILVER_CHEST] + 2 * [rewards.GOLD_CHEST],
            3 * [rewards.GOLD_CHEST],
            2 * [rewards.GOLD_CHEST] + 1 * [rewards.DIAMOND_CHEST],
            1 * [rewards.GOLD_CHEST] + 2 * [rewards.DIAMOND_CHEST],
            3 * [rewards.DIAMOND_CHEST],
        ]
        return zip(chances_of_n_wins, rewards_of_n_wins)


class LoseAllGamesDraftEvaluator(DraftEvaluator):
    """A draft where all games are lost."""

    def __init__(self, card_data):
        no_wins_gold = self._get_no_wins_gold()
        super().__init__(card_data, no_wins_gold)

    def get_values(self) -> float:
        packs_value = self._get_packs_value()
        no_wins_value = self._get_no_wins_value()
        value = packs_value + no_wins_value
        logging.info(f"Lose all games draft value: {value}")
        return value

    def get_df_rows(self) -> t.List[PurchaseRow]:
        draft_value = self.get_values()
        return [
            self._make_row(
                "No Wins", card_draft.get_draft_pack_root_url(), draft_value,
            )
        ]

    def _get_no_wins_value(self):
        _, no_win_reward = list(self._get_win_chances_and_rewards())[0]
        return sum([reward.get_value(self.card_data) for reward in no_win_reward])

    def _get_no_wins_gold(self):
        _, no_win_reward = list(self._get_win_chances_and_rewards())[0]
        return sum([reward.gold for reward in no_win_reward])


class AverageDraftEvaluator(DraftEvaluator):
    """Evaluates a single where the player has an average win rate."""

    def __init__(self, card_data):
        average_win_gold = self._get_average_win_gold()
        super().__init__(card_data, average_win_gold)

    def get_values(self) -> float:
        packs_value = self._get_packs_value()
        average_wins_value = self._get_average_wins_value()

        value = packs_value + average_wins_value
        logging.info(f"Average draft value: {value}")
        return value

    def _get_average_wins_value(self) -> float:
        average_win_value = 0
        for chance, win_rewards in self._get_win_chances_and_rewards():
            win_value = sum(
                [reward.get_value(self.card_data) for reward in win_rewards]
            )

            average_win_value += win_value * chance
        return average_win_value

    def _get_average_win_gold(self) -> float:
        average_win_gold = 0
        for chance, win_rewards in self._get_win_chances_and_rewards():
            win_gold = sum([reward.gold for reward in win_rewards])
            average_win_gold += win_gold * chance
        return average_win_gold

    def get_df_rows(self) -> t.List[PurchaseRow]:
        draft_value = self.get_values()
        return [
            self._make_row(
                "Average Draft", card_draft.get_draft_pack_root_url(), draft_value,
            )
        ]


class LeagueEvaluator(PurchaseEvaluator, abc.ABC):
    """ABC for league purchases."""

    def __init__(self, card_data):
        super().__init__(card_data, cost=12_500, purchase_type="League")

    def get_league_packs_value(self) -> float:
        pack_counts = get_league_packs()

        pack_values = PackEvaluator(self.card_data).get_values()

        total_value = 0
        for pack, count in pack_counts.items():
            count = pack_counts[pack]
            value_per_pack = pack_values.get(pack, 0)
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
        chances_of_rank = [
            4.4e-06,
            1.95e-05,
            7.08e-05,
            0.0010323,
            0.0758747,
            0.3602328,
            0.5627655,
        ]

        rewards_of_rank = [
            20
            * [
                rewards.Reward(
                    card_classes=rewards.get_pack_contents_for_sets(
                        [models_card_set.get_newest_main_set()]
                    )
                )
            ]
            + [
                rewards.Reward(
                    card_classes=[
                        rewards.CardClass(rarity=rarity.LEGENDARY, is_premium=True)
                    ]
                )
            ],
            17
            * [
                rewards.Reward(
                    card_classes=rewards.get_pack_contents_for_sets(
                        [models_card_set.get_newest_main_set()]
                    )
                )
            ]
            + [
                rewards.Reward(
                    card_classes=[
                        rewards.CardClass(rarity=rarity.LEGENDARY, is_premium=True)
                    ]
                )
            ],
            15
            * [
                rewards.Reward(
                    card_classes=rewards.get_pack_contents_for_sets(
                        [models_card_set.get_newest_main_set()]
                    )
                )
            ]
            + [
                rewards.Reward(
                    card_classes=[
                        rewards.CardClass(rarity=rarity.LEGENDARY, is_premium=True)
                    ]
                )
            ],
            13
            * [
                rewards.Reward(
                    card_classes=rewards.get_pack_contents_for_sets(
                        [models_card_set.get_newest_main_set()]
                    )
                )
            ]
            + [
                rewards.Reward(
                    card_classes=[
                        rewards.CardClass(rarity=rarity.LEGENDARY, is_premium=True)
                    ]
                )
            ],
            12
            * [
                rewards.Reward(
                    card_classes=rewards.get_pack_contents_for_sets(
                        [models_card_set.get_newest_main_set()]
                    )
                )
            ]
            + [
                rewards.Reward(
                    card_classes=[
                        rewards.CardClass(rarity=rarity.RARE, is_premium=True)
                    ]
                )
            ],
            9
            * [
                rewards.Reward(
                    card_classes=rewards.get_pack_contents_for_sets(
                        [models_card_set.get_newest_main_set()]
                    )
                )
            ]
            + [
                rewards.Reward(
                    card_classes=[
                        rewards.CardClass(rarity=rarity.RARE, is_premium=True)
                    ]
                )
            ],
            8
            * [
                rewards.Reward(
                    card_classes=rewards.get_pack_contents_for_sets(
                        [models_card_set.get_newest_main_set()]
                    )
                )
            ]
            + [
                rewards.Reward(
                    card_classes=[
                        rewards.CardClass(rarity=rarity.RARE, is_premium=True)
                    ]
                )
            ],
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
        logging.info(f"First league value: {value}")
        return value

    def get_df_rows(self):
        first_league_value = self.get_value()
        return [
            self._make_row(
                "First of the Month",
                dwd_news.get_most_recent_league_article_url(),
                first_league_value,
            )
        ]


class AdditionalLeagueEvaluator(LeagueEvaluator):
    """Evaluates any league in a month after the first."""

    def get_value(self):
        value = self.get_league_packs_value()
        logging.info(f"Additional league value: {value}")
        return value

    def get_df_rows(self):
        additional_league_value = self.get_value()
        return [
            self._make_row(
                "Additional in the Month",
                dwd_news.get_most_recent_league_article_url(),
                additional_league_value,
            )
        ]


def get_league_packs() -> t.Dict[models_card_set.CardSet, int]:
    card_sets = models_card_set.CardSetName.query.all()
    packs = {
        models_card_set.CardSet.from_name(card_set.name): card_set.num_in_league
        for card_set in card_sets
    }
    return packs


def get_purchase_values(own_values: card_evaluation.OwnValueFrame, user: User):
    getter = _PurchasesValueDataframeGetter(own_values, user)
    return getter.get_purchase_values()


class _PurchasesValueDataframeGetter:
    """Helper class used by get_purchase_values_df."""

    def __init__(self, card_data: card_evaluation.OwnValueFrame, user: User):
        self.card_data = card_data
        self.user = user

        self.purchase_evaluators = [
            PackEvaluator(self.card_data),
            CampaignEvaluator(self.card_data),
            AverageDraftEvaluator(self.card_data),
            LoseAllGamesDraftEvaluator(self.card_data),
            FirstLeagueEvaluator(self.card_data),
            AdditionalLeagueEvaluator(self.card_data),
        ]

    def get_purchase_values(self):
        """Gets a dataframe of all purchase options
        with values based on card values."""
        columns = ["type", "name", "info_url", "gold_cost", "value", "value_per_gold"]
        df_constructor = []
        for purchase_evaluator in self.purchase_evaluators:
            df_constructor += purchase_evaluator.get_df_rows()

        values_df = pd.DataFrame(df_constructor, columns=columns)
        return values_df
