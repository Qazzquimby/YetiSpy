from infiltrate import caches, models
from infiltrate.models.card import CardId, CardDisplay


@caches.mem_cache.cache("card_displays", expire=3600)
def make_card_display(card_id: CardId):
    """Makes a CardValueDisplay, utilizing the cache to avoid repeated work."""
    card_display = CardDisplay(card_id)
    return card_display


class CardValueDisplay:
    """A bundle of raw and computed values corresponding to a card, to be used in the front end."""

    def __init__(self, card_id_with_value: models.card.CardIdWithValue):
        self.card: CardDisplay = make_card_display(card_id_with_value.card_id)

        self.count = card_id_with_value.count
        self.value = card_id_with_value.value

        cost = models.rarity.rarity_from_name[self.card.rarity].enchant
        self.value_per_shiftstone = card_id_with_value.value * 100 / cost

    def __str__(self):
        return self.card.name, self.count
