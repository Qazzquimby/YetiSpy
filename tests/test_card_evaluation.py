import pytest
import pandas as pd

import models.card
import models.deck

import card_evaluation

card_data_dict = {
    card_evaluation.PlayCountFrame.SET_NUM: {0: 0, 1: 0,},
    card_evaluation.PlayCountFrame.CARD_NUM: {0: 0, 1: 1,},
    "name": {0: "0_0", 1: "0_1"},
    "rarity": {0: "Common", 1: "Uncommon"},
    "image_url": {0: "0_0", 1: "0_1"},
    "details_url": {0: "0_0", 1: "0_1"},
    "is_in_draft_pack": {0: 0, 1: 1},
}


@pytest.fixture
def card_data():
    """A simple CardData for the cards used in the other fixtures.."""

    return models.card.CardData(df=pd.DataFrame(card_data_dict))


# PLAY COUNTS

play_counts_dict = {
    card_evaluation.PlayCountFrame.SET_NUM: {0: 0, 1: 0, 2: 0,},
    card_evaluation.PlayCountFrame.CARD_NUM: {0: 0, 1: 0, 2: 1,},
    card_evaluation.PlayCountFrame.COUNT_IN_DECK: {0: 1, 1: 2, 2: 1,},
    "name": {0: "0_0", 1: "0_0", 2: "0_1"},
    "rarity": {0: "Common", 1: "Common", 2: "Uncommon"},
    "image_url": {0: "0_0", 1: "0_0", 2: "0_1"},
    "details_url": {0: "0_0", 1: "0_0", 2: "0_1"},
    "is_in_draft_pack": {0: 0, 1: 0, 2: 1},
    card_evaluation.PlayCountFrame.PLAY_COUNT: {
        0: models.deck.AVG_COLLECTABLE_CARDS_IN_DECK * 10,
        1: models.deck.AVG_COLLECTABLE_CARDS_IN_DECK * 5,
        2: models.deck.AVG_COLLECTABLE_CARDS_IN_DECK * 1,
    },
}


@pytest.fixture
def play_counts(card_data):
    """A simple PlayCountFrame"""
    return card_evaluation.PlayCountFrame(df=pd.DataFrame(play_counts_dict))


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


# PLAY RATES
play_rates_dict = play_counts_dict.copy()
play_rates_dict.update(
    {card_evaluation.PlayRateFrame.PLAY_RATE: {0: 40.625, 1: 20.3125, 2: 4.06250,}}
)


@pytest.fixture
def play_rates():
    """A simple PlayRateFrame built to match the play_counts fixture."""
    return card_evaluation.PlayRateFrame(df=pd.DataFrame(play_rates_dict))


def test_build_play_rate_frame(play_counts, play_rates):
    sut = card_evaluation.PlayRateFrame.from_play_counts(play_counts)
    pd.testing.assert_frame_equal(sut.df, play_rates.df)


# PLAY VALUES
play_values_dict = play_rates_dict.copy()
play_values_dict.update(
    {card_evaluation.PlayValueFrame.PLAY_VALUE: {0: 100.0, 1: 50.0, 2: 10.0}}
)


@pytest.fixture
def play_values():
    """A simple PlayValueFrame built to match the play_rates fixture."""

    return card_evaluation.PlayValueFrame(df=pd.DataFrame(play_values_dict))


def test_build_play_value_frame(play_rates, play_values):
    sut = card_evaluation.PlayValueFrame.from_play_rates(play_rates)
    pd.testing.assert_frame_equal(sut.df, play_values.df)


# PLAY CRAFT EFFICIENCY
play_craft_efficiency_dict = play_values_dict.copy()
play_craft_efficiency_dict.update(
    {
        card_evaluation.PlayCraftEfficiencyFrame.CRAFT_COST: {0: 50, 1: 50, 2: 100},
        card_evaluation.PlayCraftEfficiencyFrame.PLAY_CRAFT_EFFICIENCY: {
            0: 2.0,
            1: 1.0,
            2: 0.1,
        },
    }
)


@pytest.fixture
def play_craft_efficiency():
    return card_evaluation.PlayCraftEfficiencyFrame(
        df=pd.DataFrame(play_craft_efficiency_dict)
    )


def test_build_play_craft_efficiency_frame(play_values, play_craft_efficiency):
    sut = card_evaluation.PlayCraftEfficiencyFrame.from_play_value(play_values)
    pd.testing.assert_frame_equal(sut.df, play_craft_efficiency.df)


# OWN VALUE
own_value_dict = play_craft_efficiency_dict.copy()
own_value_dict.update(
    {
        card_evaluation.OwnValueFrame.SELL_COST: {0: 1, 1: 1, 2: 10},
        card_evaluation.OwnValueFrame.RESELL_VALUE: {0: 1.5, 1: 1.5, 2: 15.0},
        card_evaluation.OwnValueFrame.OWN_VALUE: {0: 100.0, 1: 50.0, 2: 15.0},
    }
)


@pytest.fixture
def own_value():
    return card_evaluation.OwnValueFrame(df=pd.DataFrame(own_value_dict))


def test_build_own_value_frame(play_craft_efficiency, own_value):
    sut = card_evaluation.OwnValueFrame.from_play_craft_efficiency(
        play_craft_efficiency, 2
    )
    pd.testing.assert_frame_equal(sut.df, own_value.df)


# OWN CRAFT EFFICIENCY
own_craft_efficiency_dict = own_value_dict.copy()
own_craft_efficiency_dict.update(
    {
        card_evaluation.OwnCraftEfficiencyFrame.OWN_CRAFT_EFFICIENCY: {
            0: 2.0,
            1: 1.0,
            2: 0.15,
        },
    }
)


@pytest.fixture
def own_craft_efficiency():
    return card_evaluation.OwnCraftEfficiencyFrame(
        df=pd.DataFrame(own_craft_efficiency_dict)
    )


def test_build_own_craft_efficiency_frame(own_value, own_craft_efficiency):
    sut = card_evaluation.OwnCraftEfficiencyFrame.from_own_value(own_value)
    pd.testing.assert_frame_equal(sut.df, own_craft_efficiency.df)


@pytest.fixture
def _playcount_from_db():
    """This is slow and only for manual debugging."""
    user_id = 22
    import models.user
    import global_data

    user = models.user.get_by_id(user_id)
    weighted_deck_searches = user.weighted_deck_searches
    return card_evaluation.PlayCountFrame.from_weighted_deck_searches(
        weighted_deck_searches, global_data.all_cards
    )
