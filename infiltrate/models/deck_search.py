import datetime

from infiltrate.models import db
from infiltrate.models.deck import Deck


class DeckSearch(db.Model):
    __tablename__ = "deck_searches"
    id = db.Column(db.Integer, primary_key=True)
    maximum_age_days = db.Column("maximum_age_days", db.Integer())

    def get_decks(self):
        return Deck.query.filter(
            Deck.date_updated > datetime.datetime.now() - datetime.timedelta(days=self.maximum_age_days))


class WeightedDeckSearch(db.Model):
    deck_search_id = db.Column(db.Integer, db.ForeignKey('deck_searches.id'), primary_key=True)
    username = db.Column(db.String(length=20), db.ForeignKey("users.name"))
    name = db.Column("name", db.String(length=20), primary_key=True)

    weight = db.Column("weight", db.Float)
    deck_search = db.relationship('DeckSearch', uselist=False, cascade_backrefs=False)


def update():
    # todo placeholder
    deck_search = DeckSearch(maximum_age_days=25)
    weighted = WeightedDeckSearch(weight=10,
                                  name="last 25 days",
                                  deck_search=deck_search)
    db.session.merge(weighted)
    db.session.commit()


def get_deck_search(deck_search: DeckSearch) -> DeckSearch:
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


if __name__ == '__main__':
    update()
