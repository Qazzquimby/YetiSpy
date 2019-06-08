from __future__ import annotations

import typing
from abc import ABCMeta

import selenium

from eternal_collection_guide.browser import Browser
from eternal_collection_guide.card import CardCollection, Card
from eternal_collection_guide.rarities import RARITIES
from eternal_collection_guide.sets import Sets
from eternal_collection_guide.values import ValueCollection


class CardPacks:
    """All available packs of cards in Eternal"""

    def __init__(self, sets: Sets, card_collection: CardCollection, value_collection: ValueCollection):
        self._sets = sets
        self._cards = card_collection
        self._values = value_collection

        self.set_to_card_pack = self._init_set_to_card_pack()
        self.draft_pack = DraftPack(self._cards, self._values)
        self.avg_newest_pack_value = self._init_avg_newest_pack_value()
        self.avg_golden_chest_pack_value = self._init_avg_golden_chest_pack_value()

    def _init_set_to_card_pack(self) -> typing.Dict[int, CardPack]:
        set_to_card_pack = {}

        for core_set in self._sets.core_sets:
            set_pack = SetPack(core_set.name, core_set.set_num, self._cards, self._values)
            set_to_card_pack[core_set.set_num] = set_pack

        return set_to_card_pack

    def _init_avg_newest_pack_value(self):
        newest_set = self._sets.newest_core_set
        newest_pack: CardPack = self.set_to_card_pack[newest_set.set_num]
        avg_value = newest_pack.avg_value

        return avg_value

    def _init_avg_golden_chest_pack_value(self):
        old_core_sets = self._sets.core_sets[:]
        old_core_sets.remove(self._sets.newest_core_set)

        old_card_packs: typing.List[CardPack] = [self.set_to_card_pack[core_set.set_num] for core_set in
                                                 old_core_sets]

        summed_value = sum(card_pack.avg_value for card_pack in old_card_packs)
        avg_value = summed_value / len(old_card_packs)
        return avg_value


class CardPack(metaclass=ABCMeta):
    """A pack of cards in Eternal"""

    def __init__(self, name: str, card_collection: CardCollection, value_collection: ValueCollection):
        self.name = name
        self.cards = card_collection
        self.value_sets = value_collection
        self.avg_value = self._init_avg_value()

    def get_cards_in_set(self) -> typing.List[Card]:
        """Get all cards in the set the pack belongs to."""
        raise NotImplementedError

    def _init_avg_value(self):
        values_in_rarity = self._get_values_in_rarity()
        avg_value_of_rarity = self._get_avg_value_of_rarity_dict(values_in_rarity)
        avg_value_of_pack = self._get_avg_value_of_pack(avg_value_of_rarity)
        return avg_value_of_pack

    def _get_value_of_card_by_name(self, card_name):
        value_sets = self.value_sets.dict["card_name"][card_name]
        if len(value_sets) == 0:
            return 0
        value_set = value_sets[0]
        return value_set.values[0]

    def _get_values_in_rarity(self) -> typing.Dict[str, typing.List[float]]:
        cards_in_set = self.get_cards_in_set()  # type: typing.List[Card]

        values_in_rarity = {}
        for rarity in RARITIES:
            values_in_rarity[rarity] = []

        for card in cards_in_set:
            value_of_card = self._get_value_of_card_by_name(card.name)
            rarity = card.rarity
            values_in_rarity[rarity].append(value_of_card)

        return values_in_rarity

    @staticmethod
    def _get_avg_value_of_rarity_dict(values_in_rarity: typing.Dict[str, typing.List[float]]) \
            -> typing.Dict[str, float]:
        avg_value_of_rarity = {}
        for rarity in RARITIES:
            total_value = 0
            for value in values_in_rarity[rarity]:
                total_value += value
            if total_value > 0:
                total_value /= len(values_in_rarity[rarity])
            avg_value_of_rarity[rarity] = total_value
        return avg_value_of_rarity

    @staticmethod
    def _get_avg_value_of_pack(avg_value_of_rarity_dict: typing.Dict[str, float]) -> float:
        avg_value_of_pack = 0
        for rarity in RARITIES:
            avg_value_of_rarity = avg_value_of_rarity_dict[rarity]
            num_in_pack = rarity.num_in_pack
            value_of_rarity_by_chance = avg_value_of_rarity * num_in_pack
            avg_value_of_pack += value_of_rarity_by_chance

        return avg_value_of_pack


class SetPack(CardPack):
    """A card pack for a set of cards."""

    def __init__(self, name: str, set_num: int, card_collection: CardCollection, value_collection: ValueCollection):
        self.set_num = set_num
        super().__init__(name, card_collection, value_collection)

    def get_cards_in_set(self):
        cards_in_set = self.cards.get_cards_in_set(self.set_num)
        return cards_in_set


class DraftPack(CardPack):
    """The card pack used in draft mode."""
    _cards_in_set = None

    def __init__(self, card_collection: CardCollection, value_collection: ValueCollection):
        super().__init__("Draft Pack", card_collection, value_collection)

    def get_cards_in_set(self):
        """The cards that can be available in the draft pack."""
        if self._cards_in_set is None:
            self._init_cards_in_set()
        return self._cards_in_set

    def _init_cards_in_set(self):
        browser = Browser()  # fixme this is too slow. Save this data.
        browser.get("https://eternalwarcry.com/cards")

        newest_draft_pack_option = browser.safely_find(
            lambda x: x.find_element_by_css_selector('#DraftPack > option:nth-child(2)'))

        search_id = newest_draft_pack_option.get_attribute("value")

        cards = []
        page = 1

        while True:
            url = f'https://eternalwarcry.com/cards?Query=&DraftPack={search_id}&cardview=false&p={page}'
            new_cards = self._get_cards_from_page(browser, url)
            cards += new_cards
            page += 1
            if len(new_cards) == 0:
                break

        self._cards_in_set = cards

    def _get_cards_from_page(self, browser: Browser, url: str) -> typing.List[Card]:
        browser.get(url)

        try:
            card_elements = browser.safely_find(lambda x: x.find_elements_by_xpath(
                '//*[@id="body-wrapper"]/div/div/div[2]/div[2]/div[3]/div/table/tbody/tr[*]/td[1]'))
        except selenium.common.exceptions.TimeoutException:
            card_elements = []

        cards = []
        for card_element in card_elements:
            card = self._get_card_from_element(card_element)
            cards.append(card)
        return cards

    @staticmethod
    def _get_card_from_element(element) -> Card:
        element.find_elements_by_xpath('span')

        link_element = element.find_element_by_xpath('a')
        link_str = link_element.get_attribute('href')
        set_card_str = link_str.split("/")[-2]

        set_str = set_card_str.split("-")[0]
        card_str = set_card_str.split("-")[1]

        set_num = int(set_str)
        card_num = int(card_str)

        name = element.text

        rarity_element = element.find_element_by_xpath('span')
        rarity_icon_str = rarity_element.get_attribute('class')
        rarity_str = rarity_icon_str.split('-')[-1]
        rarity = rarity_str

        card = Card(set_num, card_num, name, rarity)
        return card
