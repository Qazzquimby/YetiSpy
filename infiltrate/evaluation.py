"""Gets card values from a user's weighted deck searches"""
import typing

import infiltrate.card_display
from infiltrate import caches
from infiltrate import db
from infiltrate import models


@caches.mem_cache.cache("card_displays_for_user", expires=120)
def get_displays_for_user(user: models.user.User) -> typing.List[infiltrate.card_display.CardValueDisplay]:
    values = get_user_values(user)
    displays = [infiltrate.card_display.CardValueDisplay(v) for v in values]
    return displays


def get_user_values(user: models.user.User) -> typing.List[models.card.CardIdWithValue]:
    with db.session.no_autoflush:  # Not entirely sure why this is needed #TODO try removing
        value_dict = user.get_overall_value_dict()
        values = list(value_dict)
        return values
