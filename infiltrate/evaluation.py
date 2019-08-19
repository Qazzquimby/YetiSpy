"""Gets card values from a user's weighted deck searches"""
import typing

import card_collections
import models.card
import models.user


class GetOverallValueDict:
    """Callable to get a user's value dict (card playsets to values) given their weighted deck searches."""

    def __init__(self, weighted_deck_searches):
        self.weighted_deck_searches = weighted_deck_searches

    def __call__(self):
        return self.get_overall_value_dict()

    def get_overall_value_dict(self) -> card_collections.ValueDict:
        """Gets a ValueDict for a user based on all their weighted deck searches."""
        values = self._init_value_dict()

        value_dicts = self._get_individual_value_dicts()
        for value_dict in value_dicts:
            values.add(value_dict)

        return values

    @staticmethod
    def _init_value_dict() -> card_collections.ValueDict:
        values = card_collections.ValueDict()

        for card in models.card.ALL_CARDS:
            for play_count in range(4):
                values[card.id][play_count] += 0
        return values

    def _get_individual_value_dicts(self) -> typing.List[card_collections.ValueDict]:
        """Get a list of ValueDicts for a user, each based on a single weighted deck search."""
        value_dicts = []
        for weighted_search in self.weighted_deck_searches:
            value_dict = weighted_search.get_value_dict()
            value_dicts.append(value_dict)

        return value_dicts
