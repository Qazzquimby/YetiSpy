import pandas as pd

import models.card
import models.rarity

import pytest


@pytest.fixture
def all_cards():
    mock_all_cards_df = pd.DataFrame(
        {
            "set_num": [0, 0, 0],
            "card_num": [0, 1, 2],
            "name": ["0", "1", "2"],
            "rarity": [
                models.rarity.COMMON,
                models.rarity.UNCOMMON,
                models.rarity.RARE,
            ],
            "image_url": [
                "https://cards.eternalwarcry.com/cards/full/Kaleb's_Favor.png",
                "https://cards.eternalwarcry.com/cards/full/Blazing_Renegade.png",
                "https://cards.eternalwarcry.com/cards/full/Flash_Fire.png",
            ],
            "details_url": [
                "https://eternalwarcry.com/cards/d/0-3/kalebs-favor",
                "https://eternalwarcry.com/cards/d/0-4/blazing-renegade",
                "https://eternalwarcry.com/cards/d/0-6/flash-fire",
            ],
            "is_in_draft_pack": [0, 0, 1],
        }
    )
    return models.card.AllCards(mock_all_cards_df)


def test_card_exists(all_cards):
    assert all_cards.card_exists(card_id=models.card.CardId(0, 0))
    assert not all_cards.card_exists(card_id=models.card.CardId(1, 0))
    assert not all_cards.card_exists(card_id=models.card.CardId(0, 3))
