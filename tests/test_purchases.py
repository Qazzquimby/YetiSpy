import card_evaluation
import purchases
import models.user
import models.user.owns_card
import models.rarity
import pandas as pd


def test_get_purchase_values():
    user = models.user.User(
        id=-1,
        name="test",
        weighted_deck_searches=[],
        key=None,
        cards=[
            models.user.owns_card.UserOwnsCard(
                user_id=-1, set_num=0, card_num=0, count=2
            ),
            models.user.owns_card.UserOwnsCard(
                user_id=-1, set_num=0, card_num=1, count=1
            ),
        ],
    )
    _ = purchases.get_purchase_values(
        card_evaluation.OwnValueFrame(
            [{"set_num": 0, "rarity": models.rarity.COMMON.name}]
        ),
        user,
    )

    assert False
