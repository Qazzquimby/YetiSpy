import typing as t

import infiltrate.browsers as browsers
from infiltrate import db
from infiltrate.models.card import Card, CardId


def update_draft_pack_contents():
    """Sets the is_in_draft_pack column of the cards table
    to match Eternal Warcry readings."""
    draft_card_ids = _get_draft_pack_card_ids()
    Card.query.update({"is_in_draft_pack": False})

    for card_id in draft_card_ids:
        (
            Card.query.filter(
                Card.set_num == card_id.set_num, Card.card_num == card_id.card_num
            ).update({"is_in_draft_pack": True})
        )
    db.session.commit()


def most_recent_draft_pack_json_url():
    file_name_selector = (
        "#body-wrapper > div > div > div:nth-child(2) > div > a:nth-child(1)"
    )
    file_name = browsers.get_first_text_from_url_and_selector(
        "https://eternalwarcry.com/cards/download", file_name_selector
    ).strip()
    return f"https://eternalwarcry.com/content/draftpacks/{file_name}"


def most_recent_draft_pack_cards_url():
    draft_pack_id_selector = "#DraftPack > option:nth-child(2)"
    draft_pack_id = browsers.get_first_element_from_url_and_selector(
        "https://eternalwarcry.com/cards", draft_pack_id_selector
    ).attrs["value"]
    url = f"https://eternalwarcry.com/cards?DraftPack={draft_pack_id}"
    return url


def _get_draft_pack_card_ids() -> t.List[CardId]:
    draft_pack_url = most_recent_draft_pack_json_url()
    newest_draft_pack = browsers.get_json_from_url(draft_pack_url)
    card_ids = []
    for card in newest_draft_pack:
        card_id = CardId(set_num=card["SetNumber"], card_num=card["EternalID"])
        card_ids.append(card_id)
    return card_ids
