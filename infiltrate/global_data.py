"""Shared singleton values for the views"""
import card_details
import card_evaluation
import models.card

all_cards = card_details.CardDetails(models.card.all_cards_df_from_db())
