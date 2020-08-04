"""Shared singleton values for the views"""
import card_frame_bases
import models.card

all_cards = card_frame_bases.CardDetails(models.card.all_cards_df_from_db())
