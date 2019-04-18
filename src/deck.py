from __future__ import annotations

import re
import typing
from dataclasses import dataclass

from src.base_learner import BaseLearner
from src.browser import Browser
from src.card import CardLearner
from src.deck_searches import DeckSearch
from src.field_hash_collection import JsonLoadedCollection
from src.progress_printer import ProgressPrinter


class DeckCollection(JsonLoadedCollection):
    def __init__(self):
        self.deck_search = None
        super().__init__()

    def _add_to_dict(self, entry: Deck):
        self.dict["deck_id"][entry.deck_id].append(entry)
        for playset in entry.card_playsets:
            num_played = playset.num_copies
            for i in range(num_played):
                self.dict[(playset.set_num, playset.card_num)][i + 1].append(entry)

    @staticmethod
    def json_entry_to_content(json_entry: dict) -> Deck:
        playset_dicts = json_entry['card_playsets']
        playsets = []
        for playset_dict in playset_dicts:
            playset = Playset(
                playset_dict["set_num"],
                playset_dict["card_num"],
                playset_dict["num_copies"]
            )
            playsets.append(playset)

        content = Deck(
            json_entry['deck_id'],
            playsets,
            json_entry['archetype'],
            json_entry['last_updated'],
            json_entry['is_tournament'],
            json_entry['success'])
        return content


class Playset:
    def __init__(self, set_num: int, card_num: int, num_copies: int):
        self.set_num = set_num
        self.card_num = card_num
        self.num_copies = num_copies

    def __str__(self):
        return f"{self.num_copies}x {self.set_num}-{self.card_num}"

    @classmethod
    def from_export_text(cls, text) -> typing.Optional[Playset]:
        numbers = [int(number) for number in re.findall(r'\d+', text)]
        if len(numbers) == 3:
            num_played = numbers[0]
            set_num = numbers[1]
            card_num = numbers[2]
            playset = Playset(set_num, card_num, num_played)
            return playset
        return None


@dataclass
class Deck:
    deck_id: str
    card_playsets: typing.List[Playset]
    archetype: str
    last_updated: str
    is_tournament: bool
    success: str

    # noinspection PyTypeChecker
    @classmethod
    def from_deck_url(cls, url: str, browser: Browser, card_learner: CardLearner) -> Deck:
        browser.get(url)
        deck_id = cls.get_id_from_url(url)
        card_playsets = cls._get_card_playsets(browser, card_learner)
        if len(card_playsets) == 0:
            return None

        archetype = cls._get_archetype(browser)
        last_updated = cls._get_last_updated(browser)
        is_tournament = cls._get_is_tournament_from_url(url)
        success = cls._get_success(browser)

        deck = Deck(deck_id, card_playsets, archetype, last_updated, is_tournament, success)

        return deck

    @staticmethod
    def get_id_from_url(url: str) -> str:
        id_deck_type_string = Deck._get_id_deck_type_string_from_url(url)
        deck_id = id_deck_type_string.split("/")[0]
        return deck_id

    @staticmethod
    def _get_is_tournament_from_url(url: str) -> bool:
        id_deck_type_string = Deck._get_id_deck_type_string_from_url(url)
        is_tournament_string = id_deck_type_string.split("/")[1]
        return is_tournament_string == "tournament-deck"

    @staticmethod
    def _get_id_deck_type_string_from_url(url: str) -> str:
        base_url = "https://eternalwarcry.com/decks/details/"
        id_deck_type_string = url.replace(base_url, "")
        return id_deck_type_string

    @staticmethod
    def _get_card_playsets(browser: Browser, card_learner: CardLearner) -> typing.List[Playset]:
        deck_export = Deck._get_deck_export(browser)
        playsets = Deck._get_playsets_from_deck_export(deck_export, card_learner)
        return playsets

    @staticmethod
    def _get_playsets_from_deck_export(deck_export: str, card_learner: CardLearner) -> typing.List[Playset]:
        deck_export_rows = deck_export.split("\n")
        deck_export_rows = \
            [row for row in deck_export_rows if row != "--------------MARKET---------------"]

        playsets = []
        for row in deck_export_rows:
            playset = Playset.from_export_text(row)

            matching_cards = card_learner.collection.dict[playset.set_num][playset.card_num]
            if len(matching_cards) == 0:
                continue  # This is a card with no rarity and we don't care about it.

            matching_playset = Deck._get_existing_matching_playset(playset, playsets)
            if matching_playset is not None:
                matching_playset.num_copies += playset.num_copies
            else:
                playsets.append(playset)

        return playsets

    @staticmethod
    def _get_existing_matching_playset(playset: Playset, playsets: typing.List[Playset]) -> typing.Optional[Playset]:
        for other_playset in playsets:
            sets_match = other_playset.set_num == playset.set_num
            card_nums_match = other_playset.card_num == playset.card_num
            if sets_match and card_nums_match:
                return other_playset
        return None

    @staticmethod
    def _get_deck_export(browser: Browser) -> str:
        # Browser must already be at deck url

        deck_export_text_area = browser.find_element_by_xpath('//*[@id="export-deck-text"]')
        deck_export = deck_export_text_area.get_attribute("values")
        return deck_export

    @staticmethod
    def _get_archetype(browser) -> str:
        archetype = browser.find_element_by_xpath('//*[@id="deck-details"]/div[10]/div[2]').text
        return archetype

    @staticmethod
    def _get_success(browser) -> str:
        success = browser.find_element_by_xpath('//*[@id="deck-information-wrapper"]/div[2]').text
        return success

    @staticmethod
    def _get_last_updated(browser) -> str:
        last_updated = browser.find_element_by_xpath('//*[@id="deck-details"]/div[11]/div[2]').text
        return last_updated


class DeckLearner(BaseLearner):
    def __init__(self, file_prefix: str, deck_search: DeckSearch):
        self.deck_search = deck_search

        super().__init__(file_prefix, f"{self.deck_search.name}/decks.json", DeckCollection)
        self.collection.deck_search = self.deck_search

    def _update_collection(self):
        with Browser() as browser:
            self._find_new_decks(browser)

    def _find_new_decks(self, browser: Browser):

        card_learner = CardLearner(self.json_interface.file_prefix)

        deck_urls = self._get_deck_urls(browser)

        new_deck_ids = [Deck.get_id_from_url(url) for url in deck_urls]

        self._prune_outdated_decks(new_deck_ids)

        progress_printer = ProgressPrinter(f"Updating {self.deck_search.name} decks",
                                           len(deck_urls), 50)
        for deck_url in deck_urls:
            self._process_deck_url(deck_url, browser, card_learner, progress_printer)

    def _prune_outdated_decks(self, new_deck_ids: typing.List[str]):
        pruned_collection = DeckCollection()
        for deck in self.collection.contents:
            if deck.deck_id in new_deck_ids:
                pruned_collection.append(deck)
        self.collection = pruned_collection

    def _process_deck_url(self, deck_url: str,
                          browser: Browser,
                          card_learner: CardLearner,
                          progress_printer: ProgressPrinter):

        progress_printer.maybe_print()

        deck_id = Deck.get_id_from_url(deck_url)
        matching_decks = self.collection.dict['deck_id'][deck_id]
        if len(matching_decks) > 0:
            return

        deck_data = Deck.from_deck_url(deck_url, browser, card_learner)
        if deck_data is not None:
            self.collection.append(deck_data)

    def _get_deck_urls(self, browser: Browser) -> typing.List[str]:
        page = 1
        deck_urls = []
        while True:
            url = f"{self.deck_search.url}&p={page}"
            # url = f"https://eternalwarcry.com/decks?td=1&mdb=90&p={page}"
            browser.get(url)

            deck_links = browser.find_elements_by_xpath(
                '//*[@id="body-wrapper"]/div/form[2]/div[2]/table/tbody/tr[*]/td[2]/div[1]/div/a')
            if len(deck_links) == 0:
                break

            new_deck_urls = [deck_link.get_attribute("href") for deck_link in deck_links]
            deck_urls += new_deck_urls
            page += 1
        return deck_urls
