from base_learner import BaseLearner
from browser import Browser


class Rarity(object):
    def __init__(self, rarity_id, name):
        self.id = rarity_id
        self.name = name


COMMON = "common"
UNCOMMON = "uncommon"
RARE = "rare"
LEGENDARY = "legendary"
PROMO = "promo"

RARITIES = [COMMON, UNCOMMON, RARE, LEGENDARY, PROMO]

rarity_string_to_id = {COMMON: 2,
                       UNCOMMON: 3,
                       RARE: 4,
                       LEGENDARY: 5,
                       PROMO: 6}


class CardData(object):
    def __init__(self, set_num: int, card_num: int, name: str, rarity: str):
        self.set_num = set_num
        self.card_num = card_num
        self.name = name
        self.rarity = rarity

    def __str__(self):
        return f"{self.name} - {self.set_num}, {self.card_num}"


class CardLearner(BaseLearner):
    def __init__(self, file_prefix: str):
        super().__init__(file_prefix, "cards.json")
        self.contents = self._load()

    def _update_contents(self):
        with Browser() as browser:
            for rarity in RARITIES:
                self._find_new_cards_with_rarity(rarity, browser)

    def _find_new_cards_with_rarity(self, rarity: str, browser: Browser):
        page = 1
        while True:
            is_empty = self._find_new_cards_with_rarity_on_page(rarity, page, browser)
            page += 1
            if is_empty:
                break

    def _find_new_cards_with_rarity_on_page(self, rarity: str, page, browser: Browser):
        rarity_id = rarity_string_to_id[rarity]
        url = f"https://eternalwarcry.com/cards?Rarities={rarity_id}&cardview=false&p={page}"
        browser.get(url)

        is_empty = False

        card_table = browser.find_elements_by_xpath(
            '//*[@id="body-wrapper"]/div/div/div[2]/div[2]/div[3]/div/table/tbody/tr[*]/td[1]/a'
        )
        if len(card_table) == 0:
            is_empty = True
        for card_link in card_table:
            name = card_link.text
            if len(self.contents.dict['name'][name]) == 0:
                card_url = card_link.get_attribute("href")
                set_num = self._get_set_num_from_card_url(card_url)
                card_num = self._get_card_num_from_card_url(card_url)

                card = CardData(set_num, card_num, name, rarity)
                self.contents.append(card)

        self._save()
        return is_empty

    def _get_set_num_from_card_url(self, url):
        set_card_string = self._get_set_card_string_from_card_url(url)
        set_num = int(set_card_string.split("-")[0])
        return set_num

    def _get_card_num_from_card_url(self, url):
        set_card_string = self._get_set_card_string_from_card_url(url)
        card_num = int(set_card_string.split("-")[1])
        return card_num

    def _get_set_card_string_from_card_url(self, url: str):
        base_url = 'https://eternalwarcry.com/cards/details/'
        url = url.replace(base_url, "")
        set_card_string = url.split("/")[0]
        return set_card_string

    def _json_entry_to_content(self, json_entry):
        content = CardData(json_entry['set_num'],
                           json_entry['card_num'],
                           json_entry['name'],
                           json_entry['rarity'])
        return content
