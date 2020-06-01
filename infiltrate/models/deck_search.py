"""Specifies groups of decks"""
from __future__ import annotations

import dataclasses
import datetime
import typing as t
import pandas as pd
from progiter import progiter

import card_collections
import models.card
import models.deck
from infiltrate import db
import models.rarity


class DeckSearchHasCard(db.Model):
    """A table showing the amount the playset sizes of cards
    present in the deck search"""

    decksearch_id = db.Column(
        "decksearch_id", db.Integer, db.ForeignKey("deck_searches.id"), primary_key=True
    )
    set_num = db.Column("set_num", db.Integer, primary_key=True)
    card_num = db.Column("card_num", db.Integer, primary_key=True)
    count_in_deck = db.Column(
        "count_in_deck", db.Integer, primary_key=True, nullable=False
    )
    num_decks_with_count_or_less = db.Column(
        "num_decks_with_count_or_less", db.Integer, nullable=False
    )
    __table_args__ = (
        db.ForeignKeyConstraint(
            (set_num, card_num), [models.card.Card.set_num, models.card.Card.card_num]
        ),
        {},
    )

    @staticmethod
    def as_df(decksearch_id: int) -> pd.DataFrame:
        session = db.engine.raw_connection()
        query = f"""\
            SELECT *
            FROM deck_search_has_card
            WHERE decksearch_id = {decksearch_id}"""
        df = pd.read_sql_query(query, session)
        del df["decksearch_id"]
        return df


#
# class PlayRateFrame:
#     PLAYRATE_COL = "playrate"
#
#     def __init__(self, num_decks_with_cards: PlayCountFrame, num_cards: int):
#         self.num_cards = num_cards
#         self.df = self._init_df(num_decks_with_cards)
#
#     def _init_df(self, num_decks_with_cards: PlayCountFrame):
#         # todo scale by deck popularity
#         playrates = num_decks_with_cards.df.rename(
#             columns={PlayCountFrame.NUM_DECKS_COL: self.PLAYRATE_COL}
#         )
#
#         playrates[self.PLAYRATE_COL] = (
#                 playrates[self.PLAYRATE_COL] * 10_000 / self.num_cards
#         )
#         # todo consolidate the bloat numbers.
#         return playrates


class DeckSearch(db.Model):
    """A table for a set of parameters to filter the list of all decks"""

    __tablename__ = "deck_searches"
    id = db.Column(db.Integer, primary_key=True)
    maximum_age_days = db.Column("maximum_age_days", db.Integer())
    cards: t.List[DeckSearchHasCard] = db.relationship("DeckSearchHasCard")

    def get_decks(self) -> t.List[models.deck.Deck]:
        """Returns all decks belonging to the deck search"""
        time_to_update = datetime.datetime.now() - datetime.timedelta(
            days=self.maximum_age_days
        )
        is_past_time_to_update = models.deck.Deck.date_updated > time_to_update
        decks = models.deck.Deck.query.filter(is_past_time_to_update)
        return decks

    def get_play_counts(self) -> pd.DataFrame:
        """Gets a dataframe of the number of times each copy of each card is used
        in decks in the deck search."""
        num_decks_with_cards = DeckSearchHasCard.as_df(decksearch_id=self.id)
        return num_decks_with_cards

    # def get_playrates(self) -> PlayRateFrame:
    #     """Gets a dataframe of card playrates.
    #     Playrate is roughly play count / total play count"""
    #     # todo depreciate in favor of get play counts?
    #     num_decks_with_cards = self.get_play_counts()
    #     playrates = PlayRateFrame(num_decks_with_cards, len(self.cards))
    #     return playrates

    def update_playrates(self):
        """Updates a cache of playrates representing the total frequency
        of playsets of cards in the decks.

        This cache is redundant but avoids recalculation.

        This cache can become out of date, and should be recalculated
        regularly."""
        self.delete_playrates()
        playrates = self._get_playrates()
        self._add_playrates(playrates)

    def delete_playrates(self):
        """Delete the playrate cache."""
        DeckSearchHasCard.query.filter_by(decksearch_id=self.id).delete()

    def _get_playrates(self):
        playrate = card_collections.make_card_playset_dict()
        for deck in self.get_decks():
            for card in deck.cards:
                for num_played in range(min(card.num_played, 4)):
                    playrate[card][num_played] += 1  # todo check card is right type.
        return playrate

    def _add_playrates(self, playrates: t.Dict):
        for card_id in progiter.ProgIter(playrates.keys()):
            for play_count in range(4):
                deck_search_has_card = DeckSearchHasCard(
                    decksearch_id=self.id,
                    set_num=card_id.set_num,
                    card_num=card_id.card_num,
                    count_in_deck=play_count + 1,
                    num_decks_with_count_or_less=playrates[card_id][play_count],
                )
                db.session.merge(deck_search_has_card)
                db.session.commit()


def create_deck_searches():
    # Todo at some point users may be able to make their own deck searches.
    # TODO maybe make this cleaner while merging with the
    #  create_weighted_deck_searches stuff in login

    @dataclasses.dataclass
    class _DeckSearchCreate:
        id: int
        maximum_age_days: int

    current_initial_deck_searches = [
        _DeckSearchCreate(id=1, maximum_age_days=10),
        _DeckSearchCreate(id=2, maximum_age_days=90),
        _DeckSearchCreate(id=3, maximum_age_days=30),
    ]
    deck_searches = (
        DeckSearch(id=search.id, maximum_age_days=search.maximum_age_days)
        for search in current_initial_deck_searches
    )
    for search in deck_searches:
        db.session.merge(search)
    db.session.commit()


# class PlayabilityFrame:
#     PLAYABILITY = "playability"
#
#     SET_NUM = "set_num"
#     CARD_NUM = "card_num"
#     COUNT_IN_DECK = "count_in_deck"
#
#     PLAYABILITY_PER_SHIFTSTONE = "playability_per_shiftstone"
#
#     def __init__(self, df):
#         self.df = df
#
#     # def get_playability_per_shiftstone(self):
#     #     all_cards = self.get_all_cards_data()
#     #
#     #     # initial value per shiftstone is playability / shiftstone cost
#     #     all_cards[self.PLAYABILITY_PER_SHIFTSTONE] = self.get_value_per_shiftstone(
#     #         all_cards[models.card.AllCards.RARITY], all_cards[self.PLAYABILITY]
#     #     )
#     #     # value_of_shiftstone = self.get_value_of_shiftstone(all_cards)
#     #     # todo get value *of* shiftstone
#     #     #   then set the playability of all cards to
#     #     #   max(their playability, their disenchant value * value of shiftstone
#     #
#     #     return None  # todo
#
#     @staticmethod
#     def get_value_of_shiftstone(all_cards: pd.DataFrame):
#         # order by
#         return None  # todo
#
#     @staticmethod
#     @pd.np.vectorize
#     def get_value_per_shiftstone(rarity_str: str, playability: float):
#         """Get the playability / shifstone cost."""
#         cost = models.rarity.rarity_from_name[rarity_str].enchant
#         playability_per_shiftstone = playability / cost
#         return playability_per_shiftstone
#
#     def get_all_cards_data(self, all_cards) -> pd.DataFrame:
#         """Adds the data from all_cards to the playability data.
#         Used for getting shiftstone values."""
#         # todo This may be called many times, once per deck search
#         return (
#             self.df.set_index(["set_num", "card_num"])
#                 .join(all_cards.cards_df.set_index(["set_num", "card_num"]))
#                 .reset_index()
#         )
#
#     @classmethod
#     def from_weighted_deck_searches(
#             cls, weighted_deck_searches: t.List[models.deck_search.WeightedDeckSearch],
#     ) -> models.deck_search.PlayabilityFrame:
#         """Gets a dataframe of all cards with values for a user
#         based on all their weighted deck searches."""
#
#         playabilities = [
#             weighted_search.get_playabilities()
#             for weighted_search in weighted_deck_searches
#         ]
#         summed_playabilities = models.deck_search.PlayabilityFrame.concat(playabilities)
#         summed_playabilities.normalize()
#
#         # summed_playabilities.get_playability_per_shiftstone()  # todo, we don't need this now. del
#         return summed_playabilities
#
#     @classmethod
#     def from_playrates(cls, playrates: PlayRateFrame, weight: float):
#         playrates.df[PlayRateFrame.PLAYRATE_COL] *= weight
#         playrates = playrates.df.rename(
#             columns={PlayRateFrame.PLAYRATE_COL: cls.PLAYABILITY}
#         )
#
#         return cls(playrates)
#
#     @classmethod
#     def concat(cls, frames: t.List[PlayabilityFrame], ) -> PlayabilityFrame:
#         dfs = [frame.df for frame in frames]
#         combined_value_dfs = pd.concat(dfs)
#         summed_df = combined_value_dfs.groupby(
#             ["set_num", "card_num", "count_in_deck"]
#         ).sum()
#         summed_df.reset_index(inplace=True)
#         return PlayabilityFrame(summed_df)
#
#     def normalize(self):
#         """Normalizes the playability column between 1 and 100"""
#         self.df[self.PLAYABILITY] = (
#                 self.df[self.PLAYABILITY] * 100 / max(1, max(self.df[self.PLAYABILITY]))
#         )


class WeightedDeckSearch(db.Model):
    """A DeckSearch with a user given weight for its relative importance.

    Allows users to personalize their recommendations."""

    deck_search_id = db.Column(
        db.Integer, db.ForeignKey("deck_searches.id"), primary_key=True
    )
    user_id = db.Column(db.String(length=20), db.ForeignKey("users.id"))
    name = db.Column("name", db.String(length=20), primary_key=True)

    weight = db.Column("weight", db.Float)
    deck_search: DeckSearch = db.relationship(
        "DeckSearch", uselist=False, cascade_backrefs=False
    )

    # def get_playabilities(self) -> PlayabilityFrame:
    #     playrates = self.deck_search.get_playrates()
    #     playabilities = PlayabilityFrame.from_playrates(playrates, self.weight)
    #     return playabilities


def update_deck_searches():
    """Update the playrate caches of all deck searches."""
    weighted_deck_searches = WeightedDeckSearch.query.all()
    for weighted in weighted_deck_searches:
        print(f"Updating playrate cache for {weighted.name}")
        deck_search = weighted.deck_search
        deck_search.update_playrates()


def make_weighted_deck_search(deck_search: DeckSearch, weight: float, name: str):
    """Creates a weighted deck search."""
    weighted_deck_search = WeightedDeckSearch(
        deck_search=deck_search, name=name, weight=weight
    )
    db.session.merge(deck_search)
    db.session.commit()
    return weighted_deck_search


def get_default_weighted_deck_searches(user_id: int):
    """Generates the standard weighted deck searches,
    and gives them the user_id."""
    searches = [
        models.deck_search.WeightedDeckSearch(
            deck_search_id=1, user_id=user_id, name="Last 10 days", weight=0.7
        ),
        models.deck_search.WeightedDeckSearch(
            deck_search_id=3, user_id=user_id, name="Last 30 days", weight=0.23
        ),
        models.deck_search.WeightedDeckSearch(
            deck_search_id=2, user_id=user_id, name="Last 90 days", weight=0.07
        ),
    ]
    return searches
