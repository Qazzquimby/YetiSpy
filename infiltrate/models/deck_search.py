"""Specifies groups of decks"""
import datetime
import typing

from progiter import progiter

import infiltrate.card_display
import infiltrate.models.card
from infiltrate import card_collections
from infiltrate import db
from infiltrate import models


class DeckSearchHasCard(db.Model):
    """A table showing the amount the playset sizes of cards are present in the deck search"""
    decksearch_id = db.Column('decksearch_id', db.Integer, db.ForeignKey('deck_searches.id'), primary_key=True)
    set_num = db.Column('set_num', db.Integer, primary_key=True)
    card_num = db.Column('card_num', db.Integer, primary_key=True)
    count_in_deck = db.Column('count_in_deck', db.Integer, primary_key=True, nullable=False)
    num_decks_with_count_or_less = db.Column('num_decks_with_count_or_less', db.Integer, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint((set_num, card_num), [models.card.Card.set_num,
                                                                    models.card.Card.card_num]), {})


class DeckSearch(db.Model):
    """A table for a set of parameters to filter the list of all decks"""
    __tablename__ = "deck_searches"
    id = db.Column(db.Integer, primary_key=True)
    maximum_age_days = db.Column("maximum_age_days", db.Integer())
    cards = db.relationship('DeckSearchHasCard')

    def get_decks(self):
        """Returns all decks belonging to the deck search"""
        return models.deck.Deck.query.filter(
            models.deck.Deck.date_updated > datetime.datetime.now() - datetime.timedelta(days=self.maximum_age_days))

    def get_playrate_dict(self) -> card_collections.PlayrateDict:
        """Gets a PlayRateDict of [cardId][playset size] = proportional to play rate"""
        playrate_dict = card_collections.PlayrateDict()
        for card in self.cards:
            card_id = infiltrate.models.card.CardId(card_num=card.card_num, set_num=card.set_num)

            playrate = card.num_decks_with_count_or_less * 10_000 / len(self.cards)
            # /len(cards) hopefully normalizes by search size
            # *10_000 arbitrary bloat for more readable numbers

            playrate_dict[card_id][card.count_in_deck - 1] = playrate

        return playrate_dict

    def update_playrates(self):
        """Updates a cache of playrates representing the total frequency of playsets of cards in the decks.
        This cache is redundant but avoids recalculation.
        This cache can become out of date, and should be recalculated regularly."""
        self.delete_playrates()
        playrates = self._get_playrates()
        self._add_playrates(playrates)

    def delete_playrates(self):
        """Delete the playrate cache."""
        DeckSearchHasCard.query.filter_by(decksearch_id=self.id).delete()

    def _get_playrates(self):
        playrate = infiltrate.card_collections.make_card_playset_dict()
        for deck in self.get_decks():
            for card in deck.cards:
                card_id = infiltrate.models.card.CardId(set_num=card.set_num, card_num=card.card_num)
                for num_played in range(card.num_played):
                    playrate[card_id][num_played] += 1
        return playrate

    def _add_playrates(self, playrates: typing.Dict):
        for card_id in progiter.ProgIter(playrates.keys()):
            for play_count in range(4):
                deck_search_has_card = DeckSearchHasCard(
                    decksearch_id=self.id,
                    set_num=card_id.set_num,
                    card_num=card_id.card_num,
                    count_in_deck=play_count + 1,
                    num_decks_with_count_or_less=playrates[card_id][play_count])
                db.session.merge(deck_search_has_card)
                db.session.commit()


class WeightedDeckSearch(db.Model):
    """A DeckSearch with a user given weight for its relative importance.

    Allows users to personalize their recommendations."""
    deck_search_id = db.Column(db.Integer, db.ForeignKey('deck_searches.id'), primary_key=True)
    user_id = db.Column(db.String(length=20), db.ForeignKey("users.id"))
    name = db.Column("name", db.String(length=20), primary_key=True)

    weight = db.Column("weight", db.Float)
    deck_search = db.relationship('DeckSearch', uselist=False, cascade_backrefs=False)

    def get_value_dict(self) -> card_collections.ValueDict:
        playrate_dict = self.deck_search.get_playrate_dict()

        value_dict = card_collections.ValueDict()

        for key in playrate_dict.keys():
            for playrate in range(4):
                value_dict[key][playrate] = playrate_dict[key][playrate] * self.weight

        return value_dict


def update_deck_searches():
    """Update the playrate caches of all deck searches."""
    # todo placeholder

    weighted_deck_searches = WeightedDeckSearch.query.filter_by(user_id=0).all()
    for weighted in weighted_deck_searches:
        print(f"Upaditing playrate cache for {weighted.name}")
        deck_search = weighted.deck_search
        deck_search.update_playrates()


def make_weighted_deck_search(deck_search: DeckSearch, weight: float, name: str):
    """Creates a weighted deck search."""
    weighted_deck_search = WeightedDeckSearch(deck_search=deck_search, name=name, weight=weight)
    db.session.merge(deck_search)
    db.session.commit()
    return weighted_deck_search
