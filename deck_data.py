import re
import typing

from base_learner import BaseLearner
from browser import Browser
from card_data import CardLearner
from field_hash_collection import FieldHashCollection


class DeckCollection(FieldHashCollection):
    def _add_to_dict(self, input):
        self.dict["deck_id"][input.deck_id].append(input)


class CardPlayset(object):
    def __init__(self, set_num, card_num, num_played):
        self.set_num = set_num
        self.card_num = card_num
        self.num_played = num_played

    def __str__(self):
        return f"{self.num_played}x {self.set_num}-{self.card_num}"


class DeckData(object):
    def __init__(self, deck_id, card_playsets, archetype, last_updated, is_tournament,
                 success=None):
        self.deck_id = deck_id
        self.card_playsets = card_playsets
        self.last_updated = last_updated
        self.archetype = archetype
        self.is_tournament = is_tournament
        self.success = success

    # noinspection PyTypeChecker
    @classmethod
    def from_deck_url(cls, url: str, browser: Browser, card_learner: CardLearner):
        browser.get(url)
        deck_id = cls._get_id_from_url(url)
        card_playsets = cls._get_card_playsets(browser, card_learner)
        archetype = cls._get_archetype(browser)
        last_updated = cls._get_last_updated(browser)
        is_tournament = cls._get_is_tournament_from_url(url)
        success = cls._get_success(browser)

        deck = DeckData(deck_id, card_playsets, archetype, last_updated, is_tournament, success)

        return deck

    @staticmethod
    def _get_id_from_url(url: str):
        id_deck_type_string = DeckData._get_id_deck_type_string_from_url(url)
        id = id_deck_type_string.split("/")[0]
        return id

    @staticmethod
    def _get_is_tournament_from_url(url: str):
        id_deck_type_string = DeckData._get_id_deck_type_string_from_url(url)
        is_tournament_string = id_deck_type_string.split("/")[1]
        return is_tournament_string == "tournament-deck"

    @staticmethod
    def _get_id_deck_type_string_from_url(url: str):
        base_url = "https://eternalwarcry.com/decks/details/"
        id_deck_type_string = url.replace(base_url, "")
        return id_deck_type_string

    @staticmethod
    def _get_card_playsets(browser: Browser, card_learner):
        deck_export = DeckData._get_deck_export_contents(browser)
        playsets = DeckData._get_playsets_from_deck_export(deck_export, card_learner)
        return playsets

    @staticmethod
    def _get_playsets_from_deck_export(deck_export: str, card_learner: CardLearner):
        deck_export_rows = deck_export.split("\n")
        deck_export_rows = \
            [row for row in deck_export_rows if row != "--------------MARKET---------------"]

        playsets = []
        for row in deck_export_rows:
            playset = DeckData._get_playset_from_deck_export_row(row)

            matching_cards = card_learner.contents.dict[playset.set_num][playset.card_num]
            if len(matching_cards) == 0:
                continue  # This is a card with no rarity and we don't care about it.

            matching_playset = DeckData._get_existing_matching_playset(playset, playsets)
            if matching_playset is not None:
                matching_playset.num_played += playset.num_played
            else:
                playsets.append(playset)

        return playsets

    @staticmethod
    def _get_existing_matching_playset(playset: CardPlayset, playsets: typing.List[CardPlayset]):
        for other_playset in playsets:
            if other_playset.set_num == playset.set_num and other_playset.card_num == playset.card_num:
                return other_playset
        return None

    @staticmethod
    def _get_playset_from_deck_export_row(row):
        numbers = [int(number) for number in re.findall(r'\d+', row)]
        num_played = numbers[0]
        set_num = numbers[1]
        card_num = numbers[2]
        playset = CardPlayset(set_num, card_num, num_played)
        return playset

    @staticmethod
    def _get_deck_export_contents(browser: Browser):
        # Browser must already be at deck url

        deck_export_text_area = browser.find_element_by_xpath('//*[@id="export-deck-text"]')
        deck_export = deck_export_text_area.get_attribute("value")
        return deck_export

    @staticmethod
    def _get_archetype(browser):
        archetype = browser.find_element_by_xpath('//*[@id="deck-details"]/div[10]/div[2]').text
        return archetype

    @staticmethod
    def _get_success(browser):
        success = browser.find_element_by_xpath('//*[@id="deck-information-wrapper"]/div[2]').text
        return success

    @staticmethod
    def _get_last_updated(browser):
        last_updated = browser.find_element_by_xpath('//*[@id="deck-details"]/div[11]/div[2]').text
        return last_updated


class DeckLearner(BaseLearner):
    def __init__(self, file_prefix: str):
        super().__init__(file_prefix, "decks.json", DeckCollection)

    def _update_contents(self):
        with Browser() as browser:
            self._find_new_decks(browser)

    def _find_new_decks(self, browser):
        card_learner = CardLearner(self.file_prefix)

        deck_urls = self._get_deck_urls(browser)

        for deck_url in deck_urls:
            deck_id = DeckData._get_id_from_url(deck_url)
            matching_decks = self.contents.dict['deck_id'][deck_id]
            if len(matching_decks) > 0:
                continue

            deck_data = DeckData.from_deck_url(deck_url, browser, card_learner)
            self.contents.append(deck_data)

    def _get_deck_urls(self, browser):
        page = 1
        deck_urls = []
        while True:
            url = f"https://eternalwarcry.com/decks?td=1&mdb=15&p={page}"  # todo upgrade to 90days
            browser.get(url)

            deck_links = browser.find_elements_by_xpath(
                '//*[@id="body-wrapper"]/div/form[2]/div[2]/table/tbody/tr[*]/td[2]/div[1]/div/a')
            if len(deck_links) == 0:
                break

            new_deck_urls = [deck_link.get_attribute("href") for deck_link in deck_links]
            deck_urls += new_deck_urls
            page += 1
        return deck_urls

    def _json_entry_to_content(self, json_entry):
        playset_dicts = json_entry['card_playsets']
        playsets = []
        for playset_dict in playset_dicts:
            playset = CardPlayset(
                playset_dict["set_num"],
                playset_dict["card_num"],
                playset_dict["num_played"]
            )
            playsets.append(playset)

        content = DeckData(
            json_entry['deck_id'],
            playsets,
            json_entry['archetype'],
            json_entry['last_updated'],
            json_entry['is_tournament'],
            json_entry['success'])
        return content
