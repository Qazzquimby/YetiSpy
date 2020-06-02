import pytest
import pandas as pd
import models.deck

import card_evaluation


@pytest.fixture
def play_counts():
    """A simple PlayCountFrame"""
    return card_evaluation.PlayCountFrame(
        df=pd.DataFrame(
            {
                card_evaluation.PlayCountFrame.SET_NUM: {0: 0, 1: 0, 2: 0,},
                card_evaluation.PlayCountFrame.CARD_NUM: {0: 0, 1: 0, 2: 1,},
                card_evaluation.PlayCountFrame.COUNT_IN_DECK: {0: 1, 1: 2, 2: 1,},
                card_evaluation.PlayCountFrame.PLAY_COUNT: {0: 10, 1: 5, 2: 1,},
            }
        )
    )


@pytest.fixture
def play_rates():
    """A simple PlayRateFrame built to match the play_counts fixture."""
    return card_evaluation.PlayRateFrame(
        df=pd.DataFrame(
            {
                card_evaluation.PlayRateFrame.SET_NUM: {0: 0, 1: 0, 2: 0,},
                card_evaluation.PlayRateFrame.CARD_NUM: {0: 0, 1: 0, 2: 1,},
                card_evaluation.PlayRateFrame.COUNT_IN_DECK: {0: 1, 1: 2, 2: 1,},
                card_evaluation.PlayRateFrame.PLAY_COUNT: {0: 10, 1: 5, 2: 1,},
                card_evaluation.PlayRateFrame.PLAY_RATE: {
                    0: 10 * models.deck.AVG_COLLECTABLE_CARDS_IN_DECK / (10 + 5 + 1),
                    1: 5 * models.deck.AVG_COLLECTABLE_CARDS_IN_DECK / (10 + 5 + 1),
                    2: 1 * models.deck.AVG_COLLECTABLE_CARDS_IN_DECK / (10 + 5 + 1),
                },
            }
        )
    )


@pytest.fixture
def _playcount_from_db():
    """This is slow and only for manual debugging."""
    user_id = 22
    import models.user

    user = models.user.get_by_id(user_id)
    weighted_deck_searches = user.weighted_deck_searches
    return card_evaluation.PlayCountFrame.from_weighted_deck_searches(
        weighted_deck_searches
    )


def test__sum_count_dfs():
    df_a = pd.DataFrame(
        {
            "set_num": {0: 0, 1: 0,},
            "card_num": {0: 0, 1: 0,},
            "count_in_deck": {0: 1, 1: 2,},
            "num_decks_with_count_or_less": {0: 2, 1: 1,},
        }
    )
    df_b = pd.DataFrame(
        {
            "set_num": {0: 0, 1: 0,},
            "card_num": {0: 0, 1: 1,},
            "count_in_deck": {0: 1, 1: 1,},
            "num_decks_with_count_or_less": {0: 5, 1: 5,},
        }
    )

    df_result = pd.DataFrame(
        {
            "set_num": {0: 0, 1: 0, 2: 0,},
            "card_num": {0: 0, 1: 0, 2: 1,},
            "count_in_deck": {0: 1, 1: 2, 2: 1,},
            "num_decks_with_count_or_less": {0: 7, 1: 1, 2: 5,},
        }
    )

    result = card_evaluation.PlayCountFrame._sum_count_dfs([df_a, df_b])

    assert result.equals(df_result)


def test_build_play_rate_frame(play_counts, play_rates):
    sut = card_evaluation.PlayRateFrame.from_play_counts(play_counts)
    assert sut == play_rates
