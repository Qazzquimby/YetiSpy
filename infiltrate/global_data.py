"""Shared singleton values for the views"""

import models.card

all_cards = models.card.CardData(models.card.all_cards_df_from_db())
