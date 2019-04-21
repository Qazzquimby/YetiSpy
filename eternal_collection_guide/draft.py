# FIXME This doesn't use the structured form of packs. A pack could have multiple legendaries by this interpretation.

PACK_SIZE = 12

NUM_CARD_TYPES = 100
WEIGHTS = [1] * NUM_CARD_TYPES
VALUES = [100 - i for i in range(NUM_CARD_TYPES)]


def get_chance_of_card_ranking_being_nth_best_in_pack(card_ranking: int, n: int):
    chance_no_better_card_is_present = _get_chance_no_better_card_is_present(card_ranking)
    chance_card_ranking_is_present = _get_chance_card_ranking_is_present_given_no_better_card_is_present(card_ranking)

    chance_of_card_ranking_being_best_in_pack = chance_no_better_card_is_present * chance_card_ranking_is_present

    return chance_of_card_ranking_being_best_in_pack


def _get_top_num_cards_weights(num_cards: int) -> float:
    top_num_cards_weights = sum(WEIGHTS[:num_cards])
    return top_num_cards_weights


def _get_total_card_weights() -> float:
    total_card_weights = sum(WEIGHTS)
    return total_card_weights


def _get_chance_no_better_card_is_present(card_ranking) -> float:
    larger_card_weights = _get_top_num_cards_weights(card_ranking - 1)
    total_card_weights = _get_total_card_weights()

    chance_a_given_card_is_a_larger_card = larger_card_weights / total_card_weights
    chance_a_given_card_is_not_a_larger_card = 1 - chance_a_given_card_is_a_larger_card
    chance_no_card_is_a_larger_card = chance_a_given_card_is_not_a_larger_card ** PACK_SIZE

    return chance_no_card_is_a_larger_card


def _get_chance_card_ranking_is_present_given_no_better_card_is_present(card_ranking):
    chance_card_ranking_is_not_present \
        = _get_chance_card_ranking_is_not_present_given_no_better_card_is_present(card_ranking)

    return 1 - chance_card_ranking_is_not_present


def _get_chance_card_ranking_is_not_present_given_no_better_card_is_present(card_ranking):
    weight_of_card_ranking = WEIGHTS[card_ranking - 1]

    weights_of_better_cards = _get_top_num_cards_weights(card_ranking - 1)
    total_weight = (_get_total_card_weights() - weights_of_better_cards)

    chance_a_given_card_is_card_ranking = weight_of_card_ranking / total_weight

    chance_a_given_card_is_not_card_ranking = 1 - chance_a_given_card_is_card_ranking

    chance_no_card_is_card_ranking = chance_a_given_card_is_not_card_ranking ** PACK_SIZE

    return chance_no_card_is_card_ranking


def get_average_value_of_nth_best_card_in_pack(n: int) -> float:
    average_value_of_nth_best_card_in_pack = 0
    if n == 1:  # fixme
        for card_i in range(NUM_CARD_TYPES):
            value = VALUES[card_i]
            chance_of_being_best_card_in_pack = get_chance_of_card_ranking_being_nth_best_in_pack(card_i + 1)
            effective_value = value * chance_of_being_best_card_in_pack
            average_value_of_nth_best_card_in_pack += effective_value

    return average_value_of_nth_best_card_in_pack


print(get_average_value_of_nth_best_card_in_pack(1))
