"""Shared singleton values for the views"""
import card_frame_bases
import infiltrate
import models.card

infiltrate.db.create_all()
infiltrate.db.session.commit()

all_cards = card_frame_bases.CardDetails(models.card.all_cards_df_from_db())
