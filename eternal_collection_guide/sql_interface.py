"""Handles saving and loading objects to SQL"""
import os
import typing

import formencode
import sqlobject

if typing.TYPE_CHECKING:
    from sqlobject.sqlite.sqliteconnection import SQLiteConnection

DB_FILENAME = os.path.abspath('data.db')


def create_db_if_not_exist():
    with open(DB_FILENAME, "w+") as _:
        pass


connection_string = rf'sqlite:{DB_FILENAME}'
connection: SQLiteConnection = sqlobject.connectionForURI(connection_string)
sqlobject.sqlhub.processConnection = connection


class CardSet(sqlobject.SQLObject):
    name = sqlobject.StringCol(alternateID=True)


class Card(sqlobject.SQLObject):
    card_num = sqlobject.IntCol()
    name = sqlobject.StringCol(alternateID=True)
    set_num = sqlobject.ForeignKey(CardSet)
    is_draft = sqlobject.BoolCol()


class DeckSearch(sqlobject.SQLObject):
    name = sqlobject.StringCol(alternateID=True)
    url = sqlobject.StringCol()
    weight = sqlobject.FloatCol()


class Deck(sqlobject.SQLObject):
    deck_id = sqlobject.StringCol(alternateID=True)
    is_tournament = sqlobject.BoolCol()
    last_updated = sqlobject.DateCol()


class Between1And4Validator(formencode.FancyValidator):
    min = 1
    max = 4

    def _validate_python(self, value, state):
        if not min <= value <= 4:
            raise formencode.Invalid("Must be between 1 and 4 inclusive.")


class CardInclusionInDeck(sqlobject.SQLObject):
    deck = sqlobject.ForeignKey(Deck)
    card = sqlobject.ForeignKey(Card)
    num_copies = sqlobject.IntCol(validator=Between1And4Validator)


class CardPlayRateInSearch(sqlobject.SQLObject):
    card = sqlobject.ForeignKey(Card)
    card_set = sqlobject.ForeignKey(CardSet)
    deck_search = sqlobject.ForeignKey(DeckSearch)
    play_rate_1 = sqlobject.FloatCol()
    play_rate_2 = sqlobject.FloatCol()
    play_rate_3 = sqlobject.FloatCol()
    play_rate_4 = sqlobject.FloatCol()
