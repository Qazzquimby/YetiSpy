"""Shared singleton values for the views"""

import models.card

all_cards = models.card.AllCards(models.card.all_cards_df_from_db())
