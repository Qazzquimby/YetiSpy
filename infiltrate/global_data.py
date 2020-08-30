"""Shared singleton values for the views"""
import infiltrate.card_frame_bases as card_frame_bases
import infiltrate
import infiltrate.models.card as card

infiltrate.db.create_all()
infiltrate.db.session.commit()

all_cards = card_frame_bases.CardDetails(card.all_cards_df_from_db())
