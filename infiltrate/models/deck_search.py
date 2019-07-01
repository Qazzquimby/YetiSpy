import datetime
import typing

from infiltrate import card_collections
from infiltrate.models import db
from infiltrate.models.card import Card
from infiltrate.models.deck import Deck


class DeckSearchHasCard(db.Model):
    decksearch_id = db.Column('decksearch_id', db.Integer, db.ForeignKey('deck_searches.id'), primary_key=True)
    set_num = db.Column('set_num', db.Integer, primary_key=True)
    card_num = db.Column('card_num', db.Integer, primary_key=True)
    count_in_deck = db.Column('count_in_deck', db.Integer, primary_key=True, nullable=False)
    num_decks_with_count_or_less = db.Column('num_decks_with_count_or_less', db.Integer, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint([set_num, card_num], [Card.set_num, Card.card_num]), {})


class DeckSearch(db.Model):
    __tablename__ = "deck_searches"
    id = db.Column(db.Integer, primary_key=True)
    maximum_age_days = db.Column("maximum_age_days", db.Integer())
    cards = db.relationship('DeckSearchHasCard')

    def get_decks(self):
        return Deck.query.filter(
            Deck.date_updated > datetime.datetime.now() - datetime.timedelta(days=self.maximum_age_days))

    def update_playrates(self):
        self.delete_playrates()

        playrates = self._get_playrates()
        self._add_playrates(playrates)

    def delete_playrates(self):
        DeckSearchHasCard.query.filter_by(decksearch_id=self.id).delete()

    def _get_playrates(self):
        playrate = card_collections.make_card_playset_dict()
        for deck in self.get_decks():
            for card in deck.cards:
                card_id = card_collections.CardId(set_num=card.set_num, card_num=card.card_num)
                for num_played in range(card.num_played):
                    playrate[card_id][num_played] += 1
        return playrate

    def _add_playrates(self, playrates: typing.Dict):
        for card_id in playrates.keys():
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
    deck_search_id = db.Column(db.Integer, db.ForeignKey('deck_searches.id'), primary_key=True)
    username = db.Column(db.String(length=20), db.ForeignKey("users.name"))
    name = db.Column("name", db.String(length=20), primary_key=True)

    weight = db.Column("weight", db.Float)
    deck_search = db.relationship('DeckSearch', uselist=False, cascade_backrefs=False)


def update_deck_searches():
    # todo placeholder
    deck_search = DeckSearch.query.filter_by(maximum_age_days=25).first()
    if not deck_search:
        deck_search = DeckSearch(maximum_age_days=25)

    weighted = WeightedDeckSearch.query.filter_by(username="me",
                                                  weight=10,
                                                  name="last 25 days",
                                                  deck_search=deck_search).first()
    if not weighted:
        weighted = WeightedDeckSearch(weight=10,
                                      name="last 25 days",
                                      deck_search=deck_search)
        weighted = db.session.merge(weighted)
        db.session.commit()

    deck_search = weighted.deck_search
    deck_search.update_playrates()


def get_deck_search(deck_search: DeckSearch) -> DeckSearch:
    # TODO WHAT DOES THIS DO? KILL IT?
    match = DeckSearch.query.filter_by(maximum_age_days=deck_search.maximum_age_days).first()
    if match:
        return match
    else:
        db.session.merge(deck_search)
        db.session.commit()
        return deck_search


def make_weighted_deck_search(deck_search: DeckSearch, weight: float, name: str):
    deck_search = get_deck_search(deck_search)
    weighted_deck_search = WeightedDeckSearch(deck_search=deck_search, name=name, weight=weight)
    db.session.merge(deck_search)
    db.session.commit()
    return weighted_deck_search
