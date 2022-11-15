import typing as t

import infiltrate.browsers as browsers
import infiltrate.models.card as card_mod


def get_ew_cards_page_url(root_url: str, page: int):
    return root_url + f"&p={page}"


def get_card_ids_on_page_of_search(root_url: str, page: int) -> t.List[card_mod.CardId]:
    page_url = get_ew_cards_page_url(root_url=root_url, page=page)

    selector = (
        "div.card-search-results.row > div > div "
        "> table > tbody > tr > td:nth-child(1) > a"
    )

    card_elements = browsers.get_elements_from_url_and_selector(
        url=page_url, selector=selector
    )
    card_ids = [
        card_mod.CardId(
            set_num=int(element.attrs["data-set"]),
            card_num=int(element.attrs["data-eternalid"]),
        )
        for element in card_elements
    ]

    return card_ids


def get_card_ids_in_search(root_url: str) -> t.List[card_mod.CardId]:
    cards = []
    page = 1
    while True:
        cards_on_page = get_card_ids_on_page_of_search(root_url=root_url, page=page)
        if not cards_on_page:
            break
        cards += cards_on_page
        page += 1
    return cards


def get_ew_cards_root_url(expedition_id: str = "", draft_pack_id: str = ""):
    return (
        f"https://eternalwarcry.com/cards?Query="
        f"&Expedition={expedition_id}"
        f"&DraftPack={draft_pack_id}"
        f"&cardview=false"
    )
