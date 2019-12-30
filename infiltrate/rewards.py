import abc
import collections
import typing

import models.card
import models.card_sets
import models.rarity


class CardClass:
    def __init__(self, sets=None, rarities=None):
        self.sets = sets
        if self.sets is None:
            self.sets = models.card_sets.get_sets()

        self.rarities = rarities
        if self.rarities is None:
            self.rarities = models.rarity.RARITIES

    @property
    def num_cards(self) -> int:
        session = models.card.db.session
        count = (session.query(models.card.Card)
                 .filter(models.card.Card.set_num.in_(self.sets))
                 .filter(models.card.Card.rarity.in_(self.rarities))
                 .count())
        return count


class CardClassWithRate:
    def __init__(self, card_class: CardClass, rate: float):
        self.card_class = card_class
        self.rate = rate

    @property
    def chance_of_specific_card_drop_per_week(self) -> float:
        num_cards = self.card_class.num_cards
        chance = self.rate / num_cards
        return chance


class DropSource:
    def __init__(self, card_class_rates: typing.List[CardClassWithRate]):
        self.card_class_rates = card_class_rates


class DropSourceWithRate:
    def __init__(self, drop_source: DropSource, rate: float):
        self.drop_source = drop_source
        self.rate = rate


class PlayerDrops:
    def __init__(self, drop_source_rates: typing.List[DropSourceWithRate]):
        self.drop_source_rates = drop_source_rates

    @property
    def card_class_rates(self) -> typing.List[CardClassWithRate]:
        new_card_class_rates_dict = collections.defaultdict(int)

        for drop_source_rate in self.drop_source_rates:
            rate = drop_source_rate.rate

            drops_card_class_rates = drop_source_rate.drop_source.card_class_rates
            for drops_card_class_rate in drops_card_class_rates:
                drops_card_class = drops_card_class_rate.card_class

                drops_rate = drops_card_class_rate.rate
                combined_rate = rate * drops_rate

                new_card_class_rates_dict[drops_card_class] += combined_rate

        new_card_class_rates = [CardClassWithRate(card_class, new_card_class_rates_dict[card_class])
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

        self.rewards = self.get_rewards_per_week()

        self.drop_rates = self.get_drop_rates()

    def get_rewards_per_week(self):
        rewards = []
        rewards.append(RewardWithRate(FirstWinOfTheDay(), self.first_wins_per_week))

        ranked_silvers = min(3, self.ranked_wins_per_day // 3) * 7

        ranked_bronzes = (self.ranked_wins_per_day - ranked_silvers) * 7
        unranked_bronzes = (self.unranked_wins_per_day) * 7

        rewards.append(RewardWithRate(BronzeChest(), ranked_bronzes + unranked_bronzes))
        rewards.append(RewardWithRate(SilverChest(), ranked_silvers))

        return rewards

    def get_drop_rates(self):
        pass  # todo convert self.rewards into DropSourceWithRate


class Reward(abc.ABC):
    card_drop = None
    gold = None
    shiftstone = None
    pack_drop = None


class RewardWithRate:
    def __init__(self, reward: Reward, weight: float):
        self.reward = reward
        self.weight = weight


class CardDrop(Reward):
    def __init__(self, rarity: models.rarity.Rarity, is_premium: bool = False):
        self.rarity = rarity
        self.is_premium = is_premium


class WoodChest(Reward):
    gold = 24


class BronzeChest(Reward):
    gold = 40
    card_drop = CardDrop(models.rarity.COMMON)


class SilverChest(Reward):
    gold = 225
    card_drop = CardDrop(models.rarity.UNCOMMON)


class GoldChest(Reward):
    gold = 495
    pack_drop = models.card_sets.get_old_main_sets()


class FirstWinOfTheDay(Reward):
    pack_drop = models.card_sets.get_newest_main_set()


class DiamondChest(Reward):
    gold = 1850
    pack_drop = models.card_sets.get_old_main_sets()
    card_drop = CardDrop(models.rarity.UNCOMMON, is_premium=True)
