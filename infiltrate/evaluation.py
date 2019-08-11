"""Gets card values from a user's weighted deck searches"""
import typing

import card_display
import models.card as cards
import models.user as users
from infiltrate import db


def get_displays_for_user(user: users.User) -> typing.List[card_display.CardValueDisplay]:
    """Gets all card displays for the user, personalized to their values."""
    values = get_user_values(user)
    displays = [card_display.CardValueDisplay.from_card_id_with_value(v) for v in values]
    return displays


def get_user_values(user: users.User) -> typing.List[cards.CardIdWithValue]:
    """Gets the value of each playset size of each card for the user."""
    with db.session.no_autoflush:  # Not entirely sure why this is needed #TODO try removing
        value_dict = user.get_overall_value_dict()
        # TODO Check if slow
        values = list(value_dict)
        return values
