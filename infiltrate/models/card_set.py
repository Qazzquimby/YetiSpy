"""Models for sets of cards."""
import typing

import browser
import caches
import models.card
from infiltrate import db


class CardSetName(db.Model):
    """A table showing how many copies of a card a deck has"""
    set_num = db.Column('set_num', db.Integer, primary_key=True)
    name = db.Column('name', db.String(length=100))


def update():
    """Updates the database with set names for all card sets"""

    class _CardSetNameUpdater:
        def run(self):
            set_name_strings = self._get_set_name_strings()
            for set_name_string in set_name_strings:
                set_num, name = self._parse_set_name_string(set_name_string)
                self._create_set_name(set_num, name)

        def _get_set_name_strings(self):
            url = 'https://eternalwarcry.com/cards'
            xpath = '//*[@id="CardSet"]/optgroup[*]/option'
            set_name_strings = browser.get_strs_from_url_and_xpath(url, xpath)
            return set_name_strings

        def _parse_set_name_string(self, set_name_string: str
                                   ) -> typing.Tuple[int, str]:
            name = set_name_string.split(' [')[0]
            set_num = int(set_name_string.split(' [Set')[1].split(']')[0])
            return set_num, name

        def _create_set_name(self, set_num: int, name: str):
            card_set_name = CardSetName(set_num=set_num,
                                        name=name)
            db.session.merge(card_set_name)
            db.session.commit()

    updater = _CardSetNameUpdater()
    updater.run()


class CardSet:
    """A set of cards from a single release."""

    def __init__(self, set_num: typing.Union[int, typing.Iterable[int]]):
        try:
            # noinspection PyUnresolvedReferences
            set_num = set_num[0]
        except (TypeError, IndexError):
            pass
        if set_num in (0, 1):
            self.set_nums = [0, 1]
        else:
            self.set_nums = [set_num]

    @property
    def name(self):
        """The text name of the set."""
        return _get_set_name(self.set_nums[0])

    @property
    def is_campaign(self):
        """Is the set a campaign rather than a pack"""
        return set_num_is_campaign(self.set_nums[0])

    def __str__(self):
        return str(self.set_nums)

    def __eq__(self, other):
        if isinstance(other, CardSet):
            return self.set_nums == other.set_nums
        return NotImplemented

    def __hash__(self):
        return hash(tuple(self.set_nums))


@caches.mem_cache.cache("get_set_name")
def _get_set_name(set_num: int) -> str:
    name = CardSetName.query.filter(
        CardSetName.set_num == set_num).first().name
    return name


@caches.mem_cache.cache("get_set_from_name")
def get_set_from_name(name: int) -> CardSet:
    rows = CardSetName.query.filter(CardSetName.name == name).all()
    set_nums = [row.set_num for row in rows]
    card_set = CardSet(set_nums)
    return card_set


def set_num_is_campaign(set_num: int):
    """Return if the card set belongs to a campaign"""
    return 1000 < set_num


def get_set_nums_from_sets(sets: typing.List[CardSet]) -> typing.List[int]:
    set_nums = list(set([set_num for card_set in sets
                         for set_num in card_set.set_nums]))
    set_nums = [int(set_num) for set_num in set_nums]
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


def _get_sets_from_set_nums(set_nums: typing.List[int]
                            ) -> typing.List[CardSet]:
    """Return card sets. Same as set ids, but 0 and 1 are one set."""
    card_sets = [CardSet(s) for s in set_nums if s != 0]
    return card_sets


def _get_set_nums() -> typing.List[int]:
    """Return card set ids."""
    set_nums = list(
        models.card.db.session.query(models.card.Card.set_num).distinct())
    set_nums = [s[0] for s in set_nums if s[0]]
    return set_nums


if __name__ == '__main__':
    update()
