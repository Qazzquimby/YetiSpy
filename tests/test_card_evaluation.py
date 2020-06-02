import pytest
import pandas as pd
import models.deck

import card_evaluation

play_counts_dict = {
    card_evaluation.PlayCountFrame.SET_NUM: {0: 0, 1: 0, 2: 0,},
    card_evaluation.PlayCountFrame.CARD_NUM: {0: 0, 1: 0, 2: 1,},
    card_evaluation.PlayCountFrame.COUNT_IN_DECK: {0: 1, 1: 2, 2: 1,},
    card_evaluation.PlayCountFrame.PLAY_COUNT: {
        0: models.deck.AVG_COLLECTABLE_CARDS_IN_DECK * 10,
        1: models.deck.AVG_COLLECTABLE_CARDS_IN_DECK * 5,
        2: models.deck.AVG_COLLECTABLE_CARDS_IN_DECK * 1,
    },
}


@pytest.fixture
def play_counts():
    """A simple PlayCountFrame"""
    return card_evaluation.PlayCountFrame(df=pd.DataFrame(play_counts_dict))


play_rates_dict = play_counts_dict.copy()
play_rates_dict.update(
    {card_evaluation.PlayRateFrame.PLAY_RATE: {0: 40.625, 1: 20.3125, 2: 4.06250,}}
)


@pytest.fixture
def play_rates():
    """A simple PlayRateFrame built to match the play_counts fixture."""
    return card_evaluation.PlayRateFrame(df=pd.DataFrame(play_rates_dict))


play_values_dict = play_rates_dict.copy()
play_values_dict.update(
    {card_evaluation.PlayValueFrame.PLAY_VALUE: {0: 100.0, 1: 50.0, 2: 10.0}}
)


@pytest.fixture
def play_values():
    """A simple PlayValueFrame built to match the play_rates fixture."""

    return card_evaluation.PlayValueFrame(df=pd.DataFrame(play_values_dict))


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


def test_build_play_value_frame(play_rates, play_values):
    sut = card_evaluation.PlayValueFrame.from_play_rates(play_rates)
    assert sut == play_values
