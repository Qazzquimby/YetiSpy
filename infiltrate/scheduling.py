"""Handles scheduled tasks."""

import atexit

from apscheduler.schedulers.background import BackgroundScheduler

import models.card
import models.card_set
import models.deck
import models.deck_search
import models.user

UPDATES_TO_INTERVALS = {
    models.card.update_cards: 3,
    models.card_set.update: 3,
    models.deck.update_decks: 3,
    models.deck_search.update_deck_searches: 3,
}


def initial_update():
    models.card.db.create_all()
    models.card.db.session.commit()
    # models.card_set.CardSetName.query.delete()
    if len(models.card_set.CardSetName.query.all()) == 0:
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
    models.card.update_cards()
    # models.card_set.update()
    # models.deck.update_decks()
    # models.deck_search.update_deck_searches()
