import pytest
import pandas as pd

import card_evaluation


@pytest.fixture
def playcount_df():
    df = pd.DataFrame(
        {
            "set_num": {
                0: 0,
                1: 0,
                2: 0,
                3: 0,
                4: 0,
                5: 0,
                6: 0,
                7: 0,
                8: 0,
                9: 0,
                10: 0,
                11: 0,
            },
            "card_num": {
                0: 3,
                1: 3,
                2: 3,
                3: 3,
                4: 4,
                5: 4,
                6: 4,
                7: 4,
                8: 6,
                9: 6,
                10: 6,
                11: 6,
            },
            "count_in_deck": {
                0: 1,
                1: 2,
                2: 3,
                3: 4,
                4: 1,
                5: 2,
                6: 3,
                7: 4,
                8: 1,
                9: 2,
                10: 3,
                11: 4,
            },
            "num_decks_with_count_or_less": {
                0: 7.8,
                1: 5.799999999999999,
                2: 1.65,
                3: 0.5,
                4: 0.5,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 2.15,
                9: 1.15,
                10: 1.15,
                11: 0.6499999999999999,
            },
        }
    )
    return df


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
