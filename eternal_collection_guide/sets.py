import typing
from dataclasses import dataclass

from eternal_collection_guide.browser import Browser


@dataclass
class CardSet:
    name: str
    set_num: int

    @classmethod
    def from_set_selection_string(cls, set_selection_string):
        name = set_selection_string.split(" [")[0]

        set_num_string_with_end_bracket = set_selection_string.split(" [Set")[1]
        set_num_string = set_num_string_with_end_bracket.split("]")[0]
        set_num = int(set_num_string)

        return cls(name, set_num)

    def __lt__(self, other):
        return self.set_num < other.set_num

    def __eq__(self, other):
        return self.set_num == other.set_num


class Sets:
    core_sets: typing.List[CardSet] = []
    campaigns: typing.List[CardSet] = []

    def __init__(self):
        if len(self.core_sets) + len(self.campaigns) == 0:
            self._init_sets()  # todo save this and only load it when cards have changed

    @property
    def newest_core_set(self):
        return max(self.core_sets)

    def _init_sets(self):
        browser = Browser()
        browser.get('https://eternalwarcry.com/cards')
        set_elements = browser.find_elements_by_xpath('//*[@id="CardSet"]/option')
        for set_element in set_elements:
            set_selection_string = set_element.text
            card_set = CardSet.from_set_selection_string(set_selection_string)
            if 0 < card_set.set_num < 500:
                self.core_sets.append(card_set)
            elif 900 < card_set.set_num:
                self.campaigns.append(card_set)
        pass
