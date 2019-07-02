"""Contains the shared db resource for all models, and the update interface.

"""
from flask_sqlalchemy import SQLAlchemy

import infiltrate.models.card
import infiltrate.models.card_sets
import infiltrate.models.deck
import infiltrate.models.deck_search
import infiltrate.models.rarity
import infiltrate.models.user
from infiltrate import db

db: SQLAlchemy = db


def update():
    """Creates and updates all db tables.

    This should not normally need to be run, as ongoing updates are handled automatically."""

    db.create_all()
    # update_rarity()
    # update_cards()
    # update_users()
    # update_decks()
    infiltrate.models.deck_search.update_deck_searches()

    db.session.commit()


if __name__ == '__main__':
    update()
