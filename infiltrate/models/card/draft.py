import typing as t

import infiltrate.eternal_warcy_cards_browser as ew_cards
import infiltrate.browsers as browsers
from infiltrate import db
from infiltrate.models.card import Card, CardId


def update_is_in_draft_pack():
    """Sets the is_in_draft_pack column of the cards table
    to match Eternal Warcry readings."""
    Card.query.update({"is_in_draft_pack": False})

    draft_card_ids = _get_draft_pack_card_ids()
    for card_id in draft_card_ids:
        Card.query.filter(
            Card.set_num == card_id.set_num, Card.card_num == card_id.card_num
        ).update({"is_in_draft_pack": True})
    db.session.commit()


def _get_draft_pack_card_ids() -> t.List[CardId]:
    draft_pack_id = _get_draft_pack_id()
    root_url = ew_cards.get_ew_cards_root_url(draft_pack_id=draft_pack_id)
    return ew_cards.get_card_ids_in_search(root_url)


def _get_draft_pack_id():
    card_url = "https://eternalwarcry.com/cards"
    most_recent_expedition_selector = "#DraftPack > option:nth-child(2)"
    element = browsers.get_first_element_from_url_and_selector(
        url=card_url, selector=most_recent_expedition_selector
    )
    draft_pack_id = element.attrs["value"]
    return draft_pack_id
