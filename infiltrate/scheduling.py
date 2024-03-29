"""Handles scheduled tasks."""

import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler

import infiltrate.models.card as card
import infiltrate.models.card_set as card_set
import infiltrate.models.deck as deck
import infiltrate.models.deck_search as deck_search
import infiltrate.models.rarity as rarity
from infiltrate.models import chapter

UPDATES_TO_INTERVALS = {
    card.update_cards: 3,
    card_set.update: 3,
    deck.update_decks: 3,
    deck_search.update_deck_searches: 3,
    chapter.update: 3,
}


def initial_update():
    logging.info("Performing initial updates")
    card.db.create_all()
    card.db.session.commit()

    deck_search.setup()
    rarity.create_rarities()
    recurring_update()


def recurring_update():
    logging.info("Performing recurring updates")
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
    card_set.update()
    deck.update_decks()
    deck_search.update_deck_searches()
    chapter.update()
