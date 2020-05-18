"""Models for sets of cards."""
import typing

import browser
import caches
import models.card
from infiltrate import db


class CardSetName(db.Model):
    """A table matching set numbers and names"""

    set_num = db.Column("set_num", db.Integer, primary_key=True)
    name = db.Column("name", db.String(length=100))


def update():
    """Updates the database with set names for all card sets"""

    class _CardSetNameUpdater:
        def run(self):
            set_name_strings = self._get_set_name_strings()
            for set_name_string in set_name_strings:
                set_num, name = self._parse_set_name_string(set_name_string)
                self._create_set_name(set_num, name)

        def _get_set_name_strings(self):
            url = "https://eternalwarcry.com/cards"
            xpath = '//*[@id="CardSet"]/optgroup[*]/option'
            set_name_strings = browser.get_strs_from_url_and_xpath(url, xpath)
            return set_name_strings

        def _parse_set_name_string(
            self, set_name_string: str
        ) -> typing.Tuple[int, str]:
            name = set_name_string.split(" [")[0]
            set_num = int(set_name_string.split(" [Set")[1].split("]")[0])
            return set_num, name

        def _create_set_name(self, set_num: int, name: str):
            card_set_name = CardSetName(set_num=set_num, name=name)
            db.session.merge(card_set_name)
            db.session.commit()

    updater = _CardSetNameUpdater()
    updater.run()


class CardSet:
    """A set of cards from a single release."""

    def __init__(self, set_num: int):
        self.set_num = set_num
        if self.set_num == 0:
            self.set_num = 1

    @classmethod
    @caches.mem_cache.cache("get_set_from_name")
    def from_name(cls, name: str) -> "CardSet":
        """Constructs a CardSet matching the given name."""
        row = CardSetName.query.filter(CardSetName.name == name).first()
        set_num = row.set_num
        card_set = cls(set_num)
        return card_set

    @property
    def name(self) -> str:
        """The text name of the set."""
        return self.name_from_num(self.set_num)

    @classmethod
    @caches.mem_cache.cache("get_set_name")
    def name_from_num(cls, set_num: int):
        """The text name of the set corresponding to the set num."""
        name = CardSetName.query.filter(CardSetName.set_num == set_num).first().name
        return name

    @property
    def is_campaign(self) -> bool:
        """Is the set a campaign rather than a pack"""
        return self.is_campaign_from_num(self.set_num)

    @classmethod
    def is_campaign_from_num(cls, set_num: int):
        """Is the set matching the set num a campagin rather than a pack."""
        return 1000 < set_num

    def __str__(self):
        return str(self.set_num)

    def __eq__(self, other):
        if isinstance(other, CardSet):
            return self.set_num == other.set_num
        return NotImplemented

    def __hash__(self):
        return hash(self.set_num)


def get_set_nums_from_sets(sets: typing.List[CardSet]) -> typing.List[int]:
    set_nums = [card_set.set_num for card_set in sets]
    return set_nums


def get_campaign_sets() -> typing.List[CardSet]:
    """Gets all CardSets for campaigns"""
    sets = get_sets()
    campaign_sets = [card_set for card_set in sets if card_set.is_campaign]
    return campaign_sets


def get_newest_main_set() -> CardSet:
    """Gets the newest droppable pack."""
    main_sets = get_main_sets()
    newest_main_set = main_sets[-1]
    return newest_main_set


def get_old_main_sets() -> typing.List[CardSet]:
    """Gets droppable packs that are not the newest set."""
    main_sets = get_main_sets()
    return main_sets[:-1]


def get_main_sets() -> typing.List[CardSet]:
    """Gets CardSets for packs"""
    sets = get_sets()
    main_sets = [card_set for card_set in sets if not card_set.is_campaign]
    return main_sets


def get_sets() -> typing.List[CardSet]:
    """Gets all CardSets"""
    set_nums = _get_set_nums()
    sets = _get_sets_from_set_nums(set_nums)
    return sets


def _get_sets_from_set_nums(set_nums: typing.List[int]) -> typing.List[CardSet]:
    """Return card sets. Same as set ids, but 0 and 1 are one set."""
    card_sets = [CardSet(s) for s in set_nums if s != 0]
    return card_sets


def _get_set_nums() -> typing.List[int]:
    """Return card set ids."""
    set_nums = list(models.card.db.session.query(models.card.Card.set_num).distinct())
    set_nums = [s[0] for s in set_nums if s[0]]
    return set_nums


if __name__ == "__main__":
    update()
