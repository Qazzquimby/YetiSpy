"""Related to the Draft purchase option in Eternal"""
import typing

import selenium

from eternal_collection_guide.browser import Browser
from eternal_collection_guide.buy_options import BuyOption
from eternal_collection_guide.card import CardCollection, Card
from eternal_collection_guide.card_pack import CardPacks, CardPack
from eternal_collection_guide.rarities import RARITIES
from eternal_collection_guide.shiftstone import NUM_CARDS_IN_PACK, RARITY_REGULAR_DISENCHANT
from eternal_collection_guide.values import ValueCollection


class BuyDraft(BuyOption):
    """A purchase of a Draft run in Eternal."""

    def __init__(self, card_packs: CardPacks):
        self.card_packs = card_packs

        super().__init__()

        self._num_newest_packs = 2
        self._num_draft_packs = 2

        self._avg_wins = 2.4  # statistical average is ~2.8. This is slightly lower to account for collection-drafting.
        self._avg_gold_chests = self._avg_wins - 1  # only works if avg_wins between 2 and 4
        self._estimated_draft_efficiency = 1.25

    @property
    def name(self):
        return "Draft"

    @property
    def gold_cost(self) -> int:
        return 5000

    @property
    def gem_cost(self) -> int:
        return 500

    @property
    def avg_gold_output(self) -> float:
        silver_chest = 225
        gold_chest = 550
        half_chance_silver_or_gold = (225 + 550) / 2
        return silver_chest + gold_chest + half_chance_silver_or_gold

    @property
    def avg_shiftstone_output(self) -> float:
        total_shiftstone = 500  # flat value
        for rarity in RARITIES:
            num_cards = NUM_CARDS_IN_PACK[rarity]
            shiftstone_per_card = RARITY_REGULAR_DISENCHANT[rarity]
            shiftstone_for_rarity = num_cards * shiftstone_per_card
            total_shiftstone += (4 + self._avg_gold_chests) * shiftstone_for_rarity
        return total_shiftstone

    @property
    def avg_value(self) -> float:
        return self._value_of_draft_packs() + self._value_of_newest_packs() + self._value_of_gold_chests()

    def _value_of_draft_packs(self):
        value_of_draft_pack = self._estimated_draft_efficiency * self.card_packs.draft_pack.avg_value
        value_of_draft_packs = self._num_draft_packs * value_of_draft_pack
        return value_of_draft_packs

    def _value_of_newest_packs(self):
        value_of_newest_pack = self._estimated_draft_efficiency * self.card_packs.avg_newest_pack_value
        value_of_newest_packs = self._num_newest_packs * value_of_newest_pack
        return value_of_newest_packs

    def _value_of_gold_chests(self):
        return self._avg_gold_chests * self.card_packs.avg_golden_chest_pack_value


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
