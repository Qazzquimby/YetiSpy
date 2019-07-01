import typing

from infiltrate import card_collections, caches
from infiltrate import db
from infiltrate import models
from infiltrate.models import rarity
from infiltrate.models.card import Card
from infiltrate.models.deck_search import DeckSearch, WeightedDeckSearch
from infiltrate.models.user import User


@caches.mem_cache.cache("card_displays", expire=3600)
def make_card_display(card_id: card_collections.CardId):
    print(card_id)
    card_display = CardDisplay(card_id)
    return card_display


class CardDisplay:
    def __init__(self, card_id: card_collections.CardId):
        card = models.card.get_card(card_id.set_num, card_id.card_num)
        self.name = card.name
        self.rarity = card.rarity
        self.image_url = card.image_url
        self.details_url = card.details_url


class CardValueDisplay:
    def __init__(self, card_id_with_value: card_collections.CardIdWithValue):
        self.card: CardDisplay = make_card_display(card_id_with_value.card_id)

        self.count = card_id_with_value.count
        self.value = card_id_with_value.value

        cost = rarity.rarity_from_name[self.card.rarity].enchant
        self.value_per_shiftstone = card_id_with_value.value * 100 / cost


def get_displays_for_user(user: User) -> typing.List[CardValueDisplay]:
    values = get_values_for_user(user)
    displays = [CardValueDisplay(v) for v in values]
    return displays


def get_values_for_user(user: User) -> typing.List[card_collections.CardIdWithValue]:
    _normalize_weights(user)
    with db.session.no_autoflush:
        values = _get_values_for_deck_searches(user)
        return values


def _get_values_for_deck_searches(user: User):
    value_dict = _get_overall_value_dict(user)

    values = []
    for card_id in value_dict.keys():
        for play_count in range(4):
            value = card_collections.CardIdWithValue(card_id=card_id, value=value_dict[card_id][play_count],
                                                     count=play_count + 1)
            values.append(value)

    # TODO normalize all values between 0-100

    return values


def _normalize_weights(user: User):
    total_weight = sum([search.weight for search in user.weighted_deck_searches])
    for search in user.weighted_deck_searches:
        search.weight = search.weight / total_weight


def _get_overall_value_dict(user: User):
    value_dicts = _get_individual_value_dicts(user)
    values = card_collections.make_card_playset_dict()
    for value_dict in value_dicts:
        for card_id in value_dict.keys():
            for play_count in range(4):
                values[card_id][play_count] += value_dict[card_id][play_count]
    return values


def _get_individual_value_dicts(user: User):
    value_dicts = []
    for weighted_search in user.weighted_deck_searches:
        value_dict = _get_value_dict(user, weighted_search)

        value_dicts.append(value_dict)
    return value_dicts


def _get_value_dict(user: User, weighted_search: WeightedDeckSearch):
    playrate_dict = _get_playrate_dict(weighted_search.deck_search)
    unowned_playrate_dict = _get_playrate_dict_minus_collection(user, playrate_dict)
    value_dict = _get_value_dict_from_playrate_dict(weighted_search.weight, unowned_playrate_dict)
    return value_dict


def _get_playrate_dict(deck_search: DeckSearch) -> typing.Dict:
    cards = deck_search.cards

    playrate = card_collections.make_card_playset_dict()
    for card in cards:
        card_id = card_collections.CardId(card_num=card.card_num, set_num=card.set_num)
        playrate[card_id][card.count_in_deck - 1] = card.num_decks_with_count_or_less

        # for card in deck.cards:
        #     card_id = card_collections.CardId(set_num=card.set_num, card_num=card.card_num)
        #     for num_played in range(card.num_played):
        #         playrate[card_id][num_played] += 1
    return playrate


def _get_value_dict_from_playrate_dict(weight: float, playrate_dict: typing.Dict):
    value_dict = playrate_dict.copy()

    for key in value_dict.keys():
        for playrate in range(4):
            value_dict[key][playrate] *= weight

    return value_dict


def _get_playrate_dict_minus_collection(user: User, playrate_dict: typing.Dict):
    adjusted_playrate_dict = playrate_dict.copy()
    for owned_card in user.cards:
        card_id = card_collections.CardId(card_num=owned_card.card_num, set_num=owned_card.set_num)
        for num_owned in range(min(4, owned_card.count)):
            adjusted_playrate_dict[card_id][num_owned] = 0
    return adjusted_playrate_dict

# if __name__ == '__main__':
#     me = User.query.filter_by(name="me").first()
#     values = get_values_for_user(me)
#     print(values)
