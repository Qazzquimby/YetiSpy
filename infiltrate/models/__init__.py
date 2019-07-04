"""Contains the shared db resource for all models, and the update interface.

"""
import infiltrate

import infiltrate.models.card
import infiltrate.models.card_sets
import infiltrate.models.deck
import infiltrate.models.deck_search
import infiltrate.models.rarity
import infiltrate.models.user


def update():
    """Creates and updates all db tables.

    This should not normally need to be run, as ongoing updates are handled automatically."""

    infiltrate.db.create_all()
    # update_rarity()
    # infiltrate.models.card.update_cards()
    # update_users()
    infiltrate.models.deck.update_decks()
    infiltrate.models.deck_search.update_deck_searches()

    infiltrate.db.session.commit()


if __name__ == '__main__':
    update()
