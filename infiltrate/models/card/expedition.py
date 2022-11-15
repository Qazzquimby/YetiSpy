import typing as t

import infiltrate.browsers as browsers
import infiltrate.eternal_warcy_cards_browser as ew_cards
import infiltrate.models.card as card_mod
from infiltrate import db


def update_is_in_expedition():
    """Sets the is_in_expedition column of the cards table
    to match Eternal Warcry readings."""
    card_mod.Card.query.update({"is_in_expedition": False})

    expedition_card_ids = _get_expedition_card_ids()
    for card_id in expedition_card_ids:
        card_mod.Card.query.filter(
            card_mod.Card.set_num == card_id.set_num,
            card_mod.Card.card_num == card_id.card_num,
        ).update({"is_in_expedition": True})
    db.session.commit()


def _get_expedition_card_ids() -> t.List[card_mod.CardId]:
    expedition_id = _get_expedition_id()
    root_url = ew_cards.get_ew_cards_root_url(expedition_id=expedition_id)
    return ew_cards.get_card_ids_in_search(root_url)


def _get_expedition_id():
    card_url = "https://eternalwarcry.com/cards"
    most_recent_expedition_selector = "#Expedition > option"
    options = browsers.get_elements_from_url_and_selector(
        url=card_url, selector=most_recent_expedition_selector
    )
    return options[1].attrs["value"]


if __name__ == "__main__":
    result = _get_expedition_card_ids()
