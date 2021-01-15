"""Specifies groups of decks"""
from __future__ import annotations

import dataclasses
import datetime
import logging
import typing as t

import pandas as pd
from tqdm import tqdm

import infiltrate.card_collections as card_collections
import infiltrate.models.card as models_card
import infiltrate.models.deck as models_deck
from infiltrate import db


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
            (set_num, card_num), [models_card.Card.set_num, models_card.Card.card_num]
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


class DeckSearch(db.Model):
    """A table for a set of parameters to filter the list of all decks"""

    __tablename__ = "deck_searches"
    id = db.Column(db.Integer, primary_key=True)
    maximum_age_days = db.Column("maximum_age_days", db.Integer())
    cards: t.List[DeckSearchHasCard] = db.relationship("DeckSearchHasCard")

    def get_decks(self) -> t.List[models_deck.Deck]:
        """Returns all decks belonging to the deck search"""
        time_to_update = datetime.datetime.now() - datetime.timedelta(
            days=self.maximum_age_days
        )
        is_past_time_to_update = models_deck.Deck.date_updated > time_to_update
        decks = models_deck.Deck.query.filter(is_past_time_to_update)
        return decks

    def get_play_counts(self) -> pd.DataFrame:
        """Gets a dataframe of the number of times each copy of each card is used
        in decks in the deck search."""
        num_decks_with_cards = DeckSearchHasCard.as_df(decksearch_id=self.id)
        return num_decks_with_cards

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
                card_id = models_card.CardId(
                    set_num=card.set_num, card_num=card.card_num
                )
                for num_played in range(min(card.num_played, 4)):
                    playrate[card_id][num_played] += self._scale_playrate(deck)
        return playrate

    def _scale_playrate(self, deck):
        """This is the adjusted amount a card play counts for,
        scaled on the 'importance' of the deck, so that better decks have more
        influence over the play rates."""
        return deck.views

    def _add_playrates(self, playrates: t.Dict):
        rows = []
        for card_id, counts in tqdm(playrates.items(), desc="Add playrates"):
            for play_count in range(1, 5):
                deck_search_has_card = DeckSearchHasCard(
                    decksearch_id=self.id,
                    set_num=card_id.set_num,
                    card_num=card_id.card_num,
                    count_in_deck=play_count,
                    num_decks_with_count_or_less=counts[play_count - 1],
                )
                rows.append(deck_search_has_card)
        db.session.bulk_save_objects(rows)
        db.session.commit()


def create_deck_searches():
    @dataclasses.dataclass
    class _DeckSearchCreate:
        id: int
        maximum_age_days: int

    current_initial_deck_searches = [
        _DeckSearchCreate(id=1, maximum_age_days=10),
        _DeckSearchCreate(id=2, maximum_age_days=30),
        _DeckSearchCreate(id=3, maximum_age_days=90),
    ]
    deck_searches = (
        DeckSearch(id=search.id, maximum_age_days=search.maximum_age_days)
        for search in current_initial_deck_searches
    )
    for search in deck_searches:
        db.session.merge(search)
    db.session.commit()


class WeightedDeckSearch(db.Model):
    """A DeckSearch with a user given weight for its relative importance.

    Allows users to personalize their recommendations."""

    deck_search_id = db.Column(
        db.Integer, db.ForeignKey("deck_searches.id"), primary_key=True
    )
    profile_id = db.Column(db.Integer())
    name = db.Column("name", db.String(length=20), primary_key=True)

    weight = db.Column("weight", db.Float)
    deck_search: DeckSearch = db.relationship(
        "DeckSearch", uselist=False, cascade_backrefs=False
    )


def update_deck_searches():
    """Update the playrate caches of all deck searches."""
    logging.info("Updating deck_searches")
    weighted_deck_searches = WeightedDeckSearch.query.all()
    for weighted in weighted_deck_searches:
        logging.info(f"Updating playrate cache for {weighted.name}")
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


def get_weighted_deck_searches(profile=1):
    """Generates the standard weighted deck searches,
    and gives them the user_id."""

    return WeightedDeckSearch.query.filter_by(profile_id=profile).all()


def _normalize_deck_search_weights(weighted_deck_searches: t.List[WeightedDeckSearch]):
    """Ensures that a user's saved weights are approximately normalized
    to 1.
    This prevents weight sizes from inflating values."""
    total_weight = sum([search.weight for search in weighted_deck_searches])
    # Bounds prevent repeated work due to rounding on later passes
    if not 0.9 < total_weight < 1.10:
        for search in weighted_deck_searches:
            search.weight = search.weight / total_weight


def create_weighted_deck_searches():
    weighted_deck_searches = [
        WeightedDeckSearch(
            profile_id=1, deck_search_id=1, name="Last 10 days", weight=0.7
        ),
        WeightedDeckSearch(
            profile_id=1, deck_search_id=2, name="Last 30 days", weight=0.23
        ),
        WeightedDeckSearch(
            profile_id=1, deck_search_id=3, name="Last 90 days", weight=0.07
        ),
    ]
    _normalize_deck_search_weights(weighted_deck_searches)
    for wds in weighted_deck_searches:
        db.session.merge(wds)
    db.session.commit()


def setup():
    logging.info("Setting up deck searches")
    create_deck_searches()
    create_weighted_deck_searches()
