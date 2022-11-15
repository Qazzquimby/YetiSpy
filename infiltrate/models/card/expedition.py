import typing as t

import infiltrate.browsers as browsers
import infiltrate.eternal_warcy_cards_browser as ew_cards
import infiltrate.models.card as card_mod
from infiltrate import db


def update_is_in_expedition_vault():
    """Sets the is_in_expedition column of the cards table
    to match Eternal Warcry readings."""
    card_mod.Card.query.update({"is_in_expedition_vault": False})

    expedition_vault_card_ids = _get_expedition_vault_card_ids()
    for card_id in expedition_vault_card_ids:
        card_mod.Card.query.filter(
            card_mod.Card.set_num == card_id.set_num,
            card_mod.Card.card_num == card_id.card_num,
        ).update({"is_in_expedition_vault": True})
    db.session.commit()


def _get_expedition_vault_card_ids() -> t.List[card_mod.CardId]:
    vault_id = _get_expedition_vault_id()
    root_url = ew_cards.get_ew_cards_root_url(vault_or_reprint_id=vault_id)
    return ew_cards.get_card_ids_in_search(root_url)


def _get_expedition_vault_id():
    card_url = "https://eternalwarcry.com/cards"
    vault_or_reprint_options = browsers.get_elements_from_url_and_selector(
        url=card_url, selector="#DraftPack > option"
    )[1:]
    vaults = [
        option
        for option in vault_or_reprint_options
        if "Expedition Vault" in option.text
    ]
    first_vault = vaults[0]
    return first_vault.attrs["value"]


if __name__ == "__main__":
    result = _get_expedition_vault_card_ids()
