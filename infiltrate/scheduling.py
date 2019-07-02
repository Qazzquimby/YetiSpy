"""Handles scheduled tasks."""

import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from infiltrate import models


def schedule_updates():
    """Schedules tasks"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=models.card.update_cards, trigger="interval", days=3)
    scheduler.add_job(func=models.deck.update_decks, trigger="interval", days=3)
    scheduler.add_job(func=models.deck_search.update_deck_searches, trigger="interval", days=3)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
