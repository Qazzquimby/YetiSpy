from flask_sqlalchemy import SQLAlchemy

from infiltrate import db

# from infiltrate.models.deck import update_all_decks

db: SQLAlchemy = db


def update():
    from infiltrate.models.card import update_cards
    from infiltrate.models.rarity import update_rarity
    from infiltrate.models.user import update_users
    from infiltrate.models.deck import update_all_decks
    from infiltrate.models.deck_search import update_deck_searches

    db.create_all()
    # update_rarity()
    # update_cards()
    update_users()
    # update_decks()
    update_deck_searches()

    db.session.commit()


if __name__ == '__main__':
    update()
