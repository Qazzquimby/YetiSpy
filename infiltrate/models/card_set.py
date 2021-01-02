"""Models for sets of cards."""
import collections
import typing as t

import infiltrate.browsers as browsers
import infiltrate.caches as caches
import infiltrate.dwd_news as dwd_news
import infiltrate.models.card as card
from infiltrate import db


class CardSetName(db.Model):
    """A table matching set numbers and names"""

    set_num = db.Column("set_num", db.Integer, primary_key=True)
    name = db.Column("name", db.String(length=100))
    num_in_league = db.Column("num_in_league", db.Integer)


def update():
    """Updates the database with set names for all card sets"""

    class _CardSetNameUpdater:
        def run(self):
            set_name_strings = self._get_set_name_strings()
            league_counts = self._get_league_counts()
            for set_name_string in set_name_strings:
                set_num, name = self._parse_set_name_string(set_name_string)
                league_count = league_counts.get(name, 0)
                self._create_set_name(set_num, name, league_count)

        def _get_set_name_strings(self):
            url = "https://eternalwarcry.com/cards"
            selector = "#CardSet > optgroup > option"
            set_name_strings = browsers.get_texts_from_url_and_selector(url, selector)
            return set_name_strings

        def _parse_set_name_string(self, set_name_string: str) -> t.Tuple[int, str]:
            name = set_name_string.split(" [")[0]
            set_num = int(set_name_string.split(" [Set")[1].split("]")[0])
            return set_num, name

        def _create_set_name(self, set_num: int, name: str, league_count: int):
            card_set_name = CardSetName(
                set_num=set_num, name=name, num_in_league=league_count
            )
            db.session.merge(card_set_name)
            db.session.commit()

        def _get_league_counts(self) -> t.Dict[str, int]:
            pack_texts = dwd_news.get_most_recent_league_article_packs_text()
            set_name_counter = collections.defaultdict(int)
            for pack_text in pack_texts:
                pack_text = pack_text.split(":")[-1]
                split = pack_text.split("x ")
                num_packs = int(split[0])
                set_name = split[1].strip()
                set_name_counter[set_name] += num_packs
            card_set_counter = {
                set_name: set_name_counter[set_name]
                for set_name in set_name_counter.keys()
            }
            return card_set_counter

    print("Info: Updating card sets")
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
        if row is None:
            raise ValueError(f"Card set named {name} not found in database.")
        set_num = row.set_num
        card_set = cls(set_num)
        return card_set

    @property
    def name(self) -> str:
        """The text name of the set."""
        return self.name_from_num(self.set_num)

    @property
    def image_path(self) -> str:
        return f"https://eternalwarcry.com/images/simulators/pack-set{self.set_num}.png"

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
        """Is the set matching the set num a campaign rather than a pack."""
        return 1000 < set_num

    def __str__(self):
        return str(self.set_num)

    def __eq__(self, other):
        if isinstance(other, CardSet):
            return self.set_num == other.set_num
        return NotImplemented

    def __hash__(self):
        return hash(self.set_num)


def get_set_nums_from_sets(sets: t.List[CardSet]) -> t.List[int]:
    set_nums = [card_set.set_num for card_set in sets]
    return set_nums


def get_campaign_sets() -> t.List[CardSet]:
    """Gets all CardSets for campaigns"""
    sets = get_sets()
    campaign_sets = [card_set for card_set in sets if card_set.is_campaign]
    return campaign_sets


def get_newest_main_set() -> CardSet:
    """Gets the newest droppable pack."""
    main_sets = get_main_sets()
    newest_main_set = main_sets[-1]
    return newest_main_set


def get_old_main_sets() -> t.List[CardSet]:
    """Gets droppable packs that are not the newest set."""
    main_sets = get_main_sets()
    return main_sets[:-1]


def get_main_sets() -> t.List[CardSet]:
    """Gets CardSets for packs"""
    sets = get_sets()
    main_sets = [card_set for card_set in sets if not card_set.is_campaign]
    return main_sets


def get_sets() -> t.List[CardSet]:
    """Gets all CardSets"""
    set_nums = _get_set_nums()
    sets = _get_sets_from_set_nums(set_nums)
    return sets


def _get_sets_from_set_nums(set_nums: t.List[int]) -> t.List[CardSet]:
    """Return card sets. Same as set ids, but 0 and 1 are one set."""
    card_sets = [CardSet(s) for s in set_nums if s != 0]
    return card_sets


def _get_set_nums() -> t.List[int]:
    """Return card set ids."""
    set_nums = list(card.db.session.query(card.Card.set_num).distinct())
    set_nums = [s[0] for s in set_nums if s[0]]
    return set_nums
