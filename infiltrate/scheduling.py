import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from infiltrate.models.card import update_cards
from infiltrate.models.deck import update_decks
from infiltrate.models.deck_search import update_deck_searches


def schedule_updates():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_cards, trigger="interval", days=3)
    scheduler.add_job(func=update_decks, trigger="interval", days=3)
    scheduler.add_job(func=update_deck_searches, trigger="interval", days=3)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
