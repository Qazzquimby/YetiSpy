import collections
import typing

import caches
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
            self.sets = models.card_sets.get_main_sets()

        self.rarities = rarities
        if self.rarities is None:
            self.rarities = models.rarity.RARITIES

        self.is_premium = is_premium

    @property
    def num_cards(self) -> int:
        """The total number of cards in the pool."""
        session = models.card.db.session

        sets = self.sets
        try:
            sets = [v.item() for v in sets]
        except AttributeError:
            pass

        rarities = [r.name for r in self.rarities]

        count = (session.query(models.card.Card)
                 .filter(models.card.Card.set_num.in_(sets))
                 .filter(models.card.Card.rarity.in_(rarities))
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
        one_chance = 1 / num_cards

        chance_of_none = (1 - one_chance) ** self.amount_per_week
        chance_of_at_least_one = 1 - chance_of_none
        return chance_of_at_least_one


class PlayerRewards:  # TODO Make into model to persist
    def __init__(self, first_wins_per_week, drafts_per_week,
                 ranked_wins_per_day,
                 unranked_wins_per_day):
        self.first_wins_per_week = first_wins_per_week
        self.drafts_per_week = drafts_per_week
        self.ranked_wins_per_day = ranked_wins_per_day
        self.unranked_wins_per_day = unranked_wins_per_day

        self.rewards_with_rates = self.get_rewards_per_week()

        # This could be its own object PlayerDrops
        self.card_classes_with_amounts_per_week = self.get_card_classes_with_amounts_per_week()

    def get_rewards_per_week(self):
        rewards_with_rates = []
        rewards_with_rates.append(RewardWithDropsPerWeek(FIRST_WIN_OF_THE_DAY, self.first_wins_per_week))

        ranked_silvers = min(3, self.ranked_wins_per_day // 3) * 7

        ranked_bronzes = (self.ranked_wins_per_day * 7) - ranked_silvers
        unranked_bronzes = self.unranked_wins_per_day * 7

        rewards_with_rates.append(RewardWithDropsPerWeek(BRONZE_CHEST, ranked_bronzes + unranked_bronzes))
        rewards_with_rates.append(RewardWithDropsPerWeek(SILVER_CHEST, ranked_silvers))

        # TODO add draft info
        # Draft pack pools can be found here https://eternalwarcry.com/cards/download

        # TODO Get avg chests from quests
        # TODO Get base chest drops, and reroll chest drops

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
        card_classes_with_amounts_per_week = (
            [CardClassWithAmountPerWeek(card_class=key, amount_per_week=card_classes_with_amounts_per_week_dict[key])
             for key in card_classes_with_amounts_per_week_dict.keys()])

        return card_classes_with_amounts_per_week

    @caches.mem_cache.cache(f"player_rewards_findabilities", expires=120)
    def get_chance_of_specific_card_drop_in_a_week(self, rarity: models.rarity.Rarity, set_num: int):
        chances = []
        for card_class_with_amount in self.card_classes_with_amounts_per_week:
            rarity_match = rarity in card_class_with_amount.card_class.rarities
            set_match = set_num in card_class_with_amount.card_class.sets
            if rarity_match and set_match:
                chance = card_class_with_amount.chance_of_specific_card_drop_per_week
                chances.append(chance)
        chance_of_at_least_one = get_chance_of_at_least_one(chances)
        return chance_of_at_least_one


def get_chance_of_at_least_one(probabilities):
    chance_of_none = 1
    for prob in probabilities:
        inverse = 1 - prob
        chance_of_none *= inverse
    chance_of_at_least_one = 1 - chance_of_none
    return chance_of_at_least_one


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

DEFAULT_PLAYER = PlayerRewards(first_wins_per_week=6.3,
                               drafts_per_week=0.3,
                               ranked_wins_per_day=3.5,
                               unranked_wins_per_day=0)

#
# if __name__ == '__main__':
#     #How often do you get your first win of the day? 6.7, 5, 7
#     # How many wins do you get on the average day? 3, 4
#     # Do you reroll silver chest quests? Yes, Yes, Yes
#     # How often do your quests overflow (you end the day with 3 quests)? 0, 1.5
#     # How many times do you draft per week? 1, 0, 0
#
#
#     player_rewards = PlayerRewards(first_wins_per_week=7,
#                                    drafts_per_week=0,
#                                    ranked_wins_per_day=0,
#                                    unranked_wins_per_day=1)
#
#     # Get the chance of finding Granite Coin
#     card_set = 6
#     card_rarity = models.rarity.COMMON
#     chance = player_rewards.get_chance_of_specific_card_drop_in_a_week(rarity=card_rarity, card_set=card_set)
#     print(chance)
#
#     # Get the chance of finding Granite Monument
#     card_set = 1
#     card_rarity = models.rarity.UNCOMMON
#     chance = player_rewards.get_chance_of_specific_card_drop_in_a_week(rarity=card_rarity, card_set=card_set)
#     print(chance)
#
#     # Get the chance of finding
#     card_set = 7
#     card_rarity = models.rarity.COMMON
#     chance = player_rewards.get_chance_of_specific_card_drop_in_a_week(rarity=card_rarity, card_set=card_set)
#     print(chance)
#
#     # Get the chance of finding Emblem of Shavka
#     card_set = 7
#     card_rarity = models.rarity.RARE
#     chance = player_rewards.get_chance_of_specific_card_drop_in_a_week(rarity=card_rarity, card_set=card_set)
#     print(chance)
#
#     print('debug')
