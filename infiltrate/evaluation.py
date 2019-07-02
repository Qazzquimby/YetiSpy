"""Gets card values from a user's weighted deck searches"""
import typing

from infiltrate import caches
from infiltrate import card_collections
from infiltrate import db
from infiltrate import models
from infiltrate.models.user import User


class UserCardEvaluator:
    def __init__(self, user):
        self.user = user
        self.values = self.get_values()

    def get_values(self):
        self._normalize_weights()
        with db.session.no_autoflush:
            values = self._get_values_for_deck_searches()
            return values

    def _normalize_weights(self):
        total_weight = sum([search.weight for search in self.user.weighted_deck_searches])
        if not 0.8 < total_weight < 1.25:  # Bounds prevent repeated work due to rounding on later passes
            for search in self.user.weighted_deck_searches:
                search.weight = search.weight / total_weight

    def _get_values_for_deck_searches(self):
        value_dict = self._get_overall_value_dict()

        values = []
        for card_id in value_dict.keys():
            for play_count in range(4):
                value = card_collections.CardIdWithValue(card_id=card_id,
                                                         value=value_dict[card_id][play_count],
                                                         count=play_count + 1)
                values.append(value)

        return values

    def _get_overall_value_dict(self):
        value_dicts = self._get_individual_value_dicts()
        values = card_collections.make_card_playset_dict()
        for value_dict in value_dicts:
            for card_id in value_dict.keys():
                for play_count in range(4):
                    values[card_id][play_count] += value_dict[card_id][play_count]
        return values

    def _get_individual_value_dicts(self):
        value_dicts = []
        for weighted_search in self.user.weighted_deck_searches:
            value_dict = self._get_value_dict(weighted_search)

            value_dicts.append(value_dict)
        return value_dicts

    def _get_value_dict(self, weighted_search: models.deck_search.WeightedDeckSearch):
        playrate_dict = self._get_playrate_dict(weighted_search.deck_search)
        unowned_playrate_dict = self._get_playrate_dict_minus_collection(playrate_dict)
        # TODO Maybe don't remove owned cards at this step, and filter them out later instead.
        # That way trends of owned cards can be viewed

        value_dict = self._get_value_dict_from_playrate_dict(weighted_search.weight,
                                                             unowned_playrate_dict)
        return value_dict

    def _get_playrate_dict(self, deck_search: models.deck_search.DeckSearch) -> typing.Dict:
        cards = deck_search.cards

        playrate = card_collections.make_card_playset_dict()
        for card in cards:
            card_id = card_collections.CardId(card_num=card.card_num, set_num=card.set_num)
            playrate[card_id][card.count_in_deck - 1] \
                = card.num_decks_with_count_or_less * 10_000 / len(cards)
            # /len(cards) hopefully normalizes by search size
            # *10_000 arbitrary bloat for more readable numbers
        return playrate

    def _get_playrate_dict_minus_collection(self, playrate_dict: typing.Dict):
        adjusted_playrate_dict = playrate_dict.copy()
        for owned_card in self.user.cards:
            card_id = card_collections.CardId(card_num=owned_card.card_num,
                                              set_num=owned_card.set_num)
            for num_owned in range(min(4, owned_card.count)):
                adjusted_playrate_dict[card_id][num_owned] = 0
        return adjusted_playrate_dict

    def _get_value_dict_from_playrate_dict(self, weight: float, playrate_dict: typing.Dict):
        value_dict = playrate_dict.copy()

        for key in value_dict.keys():
            for playrate in range(4):
                value_dict[key][playrate] *= weight

        return value_dict


@caches.mem_cache.cache("card_displays_for_user", expires=120)
def get_displays_for_user(user: User) -> typing.List[card_collections.CardValueDisplay]:
    values = get_user_values(user)
    displays = [card_collections.CardValueDisplay(v) for v in values]
    return displays


def get_user_values(user: User) -> typing.List[card_collections.CardIdWithValue]:
    getter = UserCardEvaluator(user)
    return getter.values
