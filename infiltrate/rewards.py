import abc
import collections
import typing

import models.card
import models.card_sets
import models.rarity


class CardClass:
    """A pool of cards from which drops are chosen."""

    def __init__(self, sets=None, rarities=None, is_premium=False):
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


class CardClassWithCardsPerReward:
    """The number of card drops from the Card Class per reward."""

    def __init__(self, card_class: CardClass, rate: float = 1):
        self.card_class = card_class
        self.rate = rate


class DropSource:
    """A stream of rewards that grant the given drop rates."""

    def __init__(self, card_class_rates: typing.List[CardClassWithCardsPerReward]):
        self.card_class_rates = card_class_rates


class DropSourceWithRate:
    def __init__(self, drop_source: DropSource, rate: float):
        self.drop_source = drop_source
        self.rate = rate

    # @property
    # def chance_of_specific_card_drop_per_week(self) -> float:
    #     """The probabilitiy of a specific card from the pool being found in a week."""
    #     num_cards = self.card_class.num_cards
    #     chance = self.rate / num_cards
    #     return chance

class PlayerDrops:
    def __init__(self, drop_source_rates: typing.List[DropSourceWithRate]):
        self.drop_source_rates = drop_source_rates

    @property
    def card_class_rates(self) -> typing.List[CardClassWithCardsPerReward]:
        new_card_class_rates_dict = collections.defaultdict(int)

        for drop_source_rate in self.drop_source_rates:
            rate = drop_source_rate.rate

            drops_card_class_rates = drop_source_rate.drop_source.card_class_rates
            for drops_card_class_rate in drops_card_class_rates:
                drops_card_class = drops_card_class_rate.card_class

                drops_rate = drops_card_class_rate.rate
                combined_rate = rate * drops_rate

                new_card_class_rates_dict[drops_card_class] += combined_rate

        new_card_class_rates = [CardClassWithCardsPerReward(card_class, new_card_class_rates_dict[card_class])
                                for card_class in new_card_class_rates_dict.keys()]

        return new_card_class_rates


class PlayerRewards:  # TODO Make into model to persist
    def __init__(self, first_wins_per_week, drafts_per_week,
                 ranked_wins_per_day,
                 unranked_wins_per_day):
        self.first_wins_per_week = first_wins_per_week
        self.drafts_per_week = drafts_per_week
        self.ranked_wins_per_day = ranked_wins_per_day
        self.unranked_wins_per_day = unranked_wins_per_day

        self.rewards_with_rates = self.get_rewards_per_week()

        self.drop_rates = self.get_drop_rates()

    def get_rewards_per_week(self):
        rewards_with_rates = []
        rewards_with_rates.append(RewardWithRate(FirstWinOfTheDay(), self.first_wins_per_week))

        ranked_silvers = min(3, self.ranked_wins_per_day // 3) * 7

        ranked_bronzes = (self.ranked_wins_per_day - ranked_silvers) * 7
        unranked_bronzes = (self.unranked_wins_per_day) * 7

        rewards_with_rates.append(RewardWithRate(BronzeChest(), ranked_bronzes + unranked_bronzes))
        rewards_with_rates.append(RewardWithRate(SilverChest(), ranked_silvers))

        return rewards_with_rates

    def get_drop_rates(self) -> PlayerDrops:
        blah = []
        for reward in self.rewards_with_rates:
            drop_source_with_rate = reward.reward.drop_source_with_rate()
            blah.append(drop_source_with_rate)
        pass  # todo convert self.rewards into DropSourceWithRate


class Reward(abc.ABC):
    def __init__(self, card_drop=None, gold=None, shiftstone=None, pack_drop=None):
        self.card_drop = card_drop
        self.gold = gold
        self.shiftstone = shiftstone
        self.pack_drop = pack_drop

    def drop_source_with_rate(self):
        card_classes_with_rates = []
        if self.card_drop is not None:
            card_classes_with_rates.append(self.card_drop)
            # todo add the other rewards. Also, replace this whole system its terrible?


class RewardWithRate:
    def __init__(self, reward: Reward, weight: float):
        self.reward = reward
        self.weight = weight


class WoodChest(Reward):
    gold = 24


class BronzeChest(Reward):
    gold = 40
    card_drop = CardClass(rarities=[models.rarity.COMMON])


class SilverChest(Reward):
    gold = 225
    card_drop = CardClass(rarities=[models.rarity.UNCOMMON])


class GoldChest(Reward):
    gold = 495
    pack_drop = models.card_sets.get_old_main_sets()


class FirstWinOfTheDay(Reward):
    pack_drop = models.card_sets.get_newest_main_set()


class DiamondChest(Reward):
    gold = 1850
    pack_drop = models.card_sets.get_old_main_sets()
    card_drop = CardClass(rarities=models.rarity.UNCOMMON, is_premium=True)


if __name__ == '__main__':
    player_rewards = PlayerRewards(first_wins_per_week=7,
                                   drafts_per_week=0,
                                   ranked_wins_per_day=0,
                                   unranked_wins_per_day=1)

    print('debug')
