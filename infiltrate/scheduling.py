"""Handles scheduled tasks."""

import atexit

from apscheduler.schedulers.background import BackgroundScheduler

import infiltrate.models.card as card
import infiltrate.models.card_set as card_set
import infiltrate.models.deck as deck
import infiltrate.models.deck_search as deck_search
import infiltrate.models.rarity

UPDATES_TO_INTERVALS = {
    card.update_cards: 3,
    card_set.update: 3,
    deck.update_decks: 3,
    deck_search.update_deck_searches: 3,
}


def initial_update():
    card.db.create_all()
    card.db.session.commit()

    deck_search.setup()
    infiltrate.models.rarity.create_rarities()

    if len(card_set.CardSetName.query.all()) == 0:
        for update in UPDATES_TO_INTERVALS.keys():
            update()


def schedule_updates():
    """Schedules tasks"""
    # Todo move the details to a config file.
    scheduler = BackgroundScheduler()
    for update, interval in UPDATES_TO_INTERVALS.items():
        scheduler.add_job(func=update, trigger="interval", days=interval)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    card.update_cards()
    # card_set.update()
    # deck.update_decks()
    # deck_search.update_deck_searches()
