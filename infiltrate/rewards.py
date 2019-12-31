import collections
import typing

import models.card
import models.card_sets
import models.rarity


class CardClass:
    """A pool of cards from which drops are chosen."""

    def __init__(self, sets: typing.Optional[typing.List[int]] = None,
                 rarities: typing.Optional[typing.List[models.rarity.Rarity]] = None,
                 is_premium=False):
        self.sets = sets
        if self.sets is None:
            self.sets = models.card_sets.get_sets()

        self.rarities = rarities
        if self.rarities is None:
            self.rarities = models.rarity.RARITIES

        self.is_premium = is_premium

    @property
    def num_cards(self) -> int:
        """The total number of cards in the pool."""
        session = models.card.db.session
        count = (session.query(models.card.Card)
                 .filter(models.card.Card.set_num.in_(self.sets))
                 .filter(models.card.Card.rarity.in_(self.rarities))
                 .count())
        return count

    def __eq__(self, other):
        is_equal = (self.sets == other.sets
                    and self.rarities == other.rarities
                    and self.is_premium == other.is_premium)
        return is_equal

    def __hash__(self):
        sets = tuple(self.sets)
        rarities = tuple(self.rarities)
        hash_value = hash((sets, rarities, self.is_premium))
        return hash_value


class CardClassWithAmount:
    """The number of card drops from the Card Class per reward."""

    def __init__(self, card_class: CardClass, amount: float = 1):
        self.card_class = card_class
        self.amount = amount


class CardClassWithAmountPerWeek:
    """The number of card drops from the Card Class found per week on average."""

    def __init__(self, card_class: CardClass, amount_per_week: float):
        self.card_class = card_class
        self.amount_per_week = amount_per_week

    @property
    def chance_of_specific_card_drop_per_week(self) -> float:
        """The probability of a specific card from the pool being found in a week."""
        num_cards = self.card_class.num_cards
        chance = self.amount_per_week / num_cards
        return chance


# class DropSource:
#     """A stream of rewards that grant the given drop rates."""
#
#     def __init__(self, card_class_rates: typing.List[CardClassWithAmount]):
#         self.card_class_rates = card_class_rates
#
#
# class DropSourceWithRate:
#     def __init__(self, drop_source: DropSource, rate: float):
#         self.drop_source = drop_source
#         self.rate = rate

# @property
# def chance_of_specific_card_drop_per_week(self) -> float:
#     """The probabilitiy of a specific card from the pool being found in a week."""
#     num_cards = self.card_class.num_cards
#     chance = self.rate / num_cards
#     return chance

#
# class PlayerDrops:
#     def __init__(self, drop_source_rates: typing.List[DropSourceWithRate]):
#         self.drop_source_rates = drop_source_rates
#
#     @property
#     def card_class_rates(self) -> typing.List[CardClassWithAmount]:
#         new_card_class_rates_dict = collections.defaultdict(int)
#
#         for drop_source_rate in self.drop_source_rates:
#             rate = drop_source_rate.rate
#
#             drops_card_class_rates = drop_source_rate.drop_source.card_class_rates
#             for drops_card_class_rate in drops_card_class_rates:
#                 drops_card_class = drops_card_class_rate.card_class
#
#                 drops_rate = drops_card_class_rate.rate
#                 combined_rate = rate * drops_rate
#
#                 new_card_class_rates_dict[drops_card_class] += combined_rate
#
#         new_card_class_rates = [CardClassWithAmount(card_class, new_card_class_rates_dict[card_class])
#                                 for card_class in new_card_class_rates_dict.keys()]
#
#         return new_card_class_rates


class PlayerRewards:  # TODO Make into model to persist
    def __init__(self, first_wins_per_week, drafts_per_week,
                 ranked_wins_per_day,
                 unranked_wins_per_day):
        self.first_wins_per_week = first_wins_per_week
        self.drafts_per_week = drafts_per_week
        self.ranked_wins_per_day = ranked_wins_per_day
        self.unranked_wins_per_day = unranked_wins_per_day

        self.rewards_with_rates = self.get_rewards_per_week()

        self.drop_rates = self.get_card_classes_with_amounts_per_week()

    def get_rewards_per_week(self):
        rewards_with_rates = []
        rewards_with_rates.append(RewardWithDropsPerWeek(FIRST_WIN_OF_THE_DAY, self.first_wins_per_week))

        ranked_silvers = min(3, self.ranked_wins_per_day // 3) * 7

        ranked_bronzes = (self.ranked_wins_per_day - ranked_silvers) * 7
        unranked_bronzes = (self.unranked_wins_per_day) * 7

        rewards_with_rates.append(RewardWithDropsPerWeek(BRONZE_CHEST, ranked_bronzes + unranked_bronzes))
        rewards_with_rates.append(RewardWithDropsPerWeek(SILVER_CHEST, ranked_silvers))

        return rewards_with_rates

    def get_card_classes_with_amounts_per_week(self) -> typing.List[CardClassWithAmountPerWeek]:
        card_classes_with_amounts_per_week_dict = collections.defaultdict(int)
        for reward_with_rate in self.rewards_with_rates:
            drops_per_week = reward_with_rate.drops_per_week

            card_classes_with_amounts = reward_with_rate.reward.card_classes_with_amounts

            for card_class_with_amount in card_classes_with_amounts:
                card_class = card_class_with_amount.card_class
                amount = card_class_with_amount.amount
                card_classes_with_amounts_per_week_dict[card_class] += amount * drops_per_week
        card_classes_with_amounts_per_week = list(card_classes_with_amounts_per_week_dict)
        return card_classes_with_amounts_per_week


class Reward:
    def __init__(self, card_classes_with_amounts=None, gold=0, shiftstone=0):
        self.card_classes_with_amounts = card_classes_with_amounts
        if self.card_classes_with_amounts is None:
            self.card_classes_with_amounts = []

        self.gold = gold
        self.shiftstone = shiftstone

    def __eq__(self, other):
        is_equal = (self.card_classes_with_amounts == other.card_classes_with_amounts
                    and self.gold == other.gold
                    and self.shiftstone == other.shiftstone
                    )
        return is_equal


def get_card_classes_with_amounts_for_sets(sets):
    card_classes_with_amounts = [
        CardClassWithAmount(card_class=CardClass(rarities=[models.rarity.COMMON],
                                                 sets=sets),
                            amount=8),
        CardClassWithAmount(card_class=CardClass(rarities=[models.rarity.UNCOMMON],
                                                 sets=sets),
                            amount=3),
        CardClassWithAmount(card_class=CardClass(rarities=[models.rarity.RARE],
                                                 sets=sets),
                            amount=0.9),
        CardClassWithAmount(card_class=CardClass(rarities=[models.rarity.LEGENDARY],
                                                 sets=sets),
                            amount=0.1)
    ]
    return card_classes_with_amounts


class RewardWithDropsPerWeek:
    def __init__(self, reward: Reward, drops_per_week: float):
        self.reward = reward
        self.drops_per_week = drops_per_week


WOOD_CHEST = Reward(gold=24)
BRONZE_CHEST = Reward(gold=40,
                      card_classes_with_amounts=[
                          CardClassWithAmount(card_class=CardClass(rarities=[models.rarity.COMMON]))
                      ])
SILVER_CHEST = Reward(gold=225,
                      card_classes_with_amounts=[
                          CardClassWithAmount(card_class=CardClass(rarities=[models.rarity.UNCOMMON]))
                      ])
GOLD_CHEST = Reward(gold=495,
                    card_classes_with_amounts=get_card_classes_with_amounts_for_sets(
                        models.card_sets.get_old_main_sets()))

DIAMOND_CHEST = Reward(gold=1850,
                       card_classes_with_amounts=(
                               get_card_classes_with_amounts_for_sets(
                                   models.card_sets.get_old_main_sets())
                               + [CardClass(rarities=models.rarity.UNCOMMON, is_premium=True)]
                       ))

FIRST_WIN_OF_THE_DAY = Reward(card_classes_with_amounts=get_card_classes_with_amounts_for_sets(
    [models.card_sets.get_newest_main_set()]
))

if __name__ == '__main__':
    player_rewards = PlayerRewards(first_wins_per_week=7,
                                   drafts_per_week=0,
                                   ranked_wins_per_day=0,
                                   unranked_wins_per_day=1)

    # Get the chance of finding Granite Coin
    card_set = 6
    card_rarity = models.rarity.COMMON

    print('debug')
