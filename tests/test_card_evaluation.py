import pytest
import pandas as pd

import infiltrate.card_frame_bases as card_frame_bases
import infiltrate.models.card as card
import infiltrate.models.deck as deck
import infiltrate.models.rarity as rarity
import infiltrate.card_evaluation as card_evaluation
import infiltrate.models.deck_search as deck_search


def test_card_copy_creates_index():
    sut = card_frame_bases.CardCopy(
        [
            {"set_num": 0, "card_num": 0, "count_in_deck": 0},
            {"set_num": 0, "card_num": 0, "count_in_deck": 2},
            {"set_num": 0, "card_num": 1, "count_in_deck": 0},
        ]
    )

    assert len(sut) == 3
    assert sut.index.nlevels == 3
    assert len(sut.columns) == 3


def test_card_details():
    sut = card_frame_bases.CardDetails(
        [
            {
                "set_num": 0,
                "card_num": 0,
                "rarity": rarity.COMMON,
                "image_url": "image_url",
                "details_url": "details_url",
                "is_in_draft_pack": "is_in_draft_pack",
            }
        ]
    )

    assert len(sut) == 1
    assert sut.index.nlevels == 2
    assert len(sut.columns) == 6


def test_play_count_frame_from_weighted_deck_searches():
    sut = card_evaluation.PlayCountFrame.from_weighted_deck_searches(
        weighted_deck_searches=[
            deck_search.WeightedDeckSearch(
                deck_search_id=0,
                user_id=0,
                name="",
                weight=1,
                deck_search=deck_search.DeckSearch(
                    id=0,
                    cards=[
                        deck_search.DeckSearchHasCard(
                            decksearch_id=0,
                            set_num=0,
                            card_num=0,
                            count_in_deck=1,
                            num_decks_with_count_or_less=2,
                        ),
                        deck_search.DeckSearchHasCard(
                            decksearch_id=0,
                            set_num=0,
                            card_num=0,
                            count_in_deck=2,
                            num_decks_with_count_or_less=1,
                        ),
                        deck_search.DeckSearchHasCard(
                            decksearch_id=0,
                            set_num=0,
                            card_num=1,
                            count_in_deck=1,
                            num_decks_with_count_or_less=1,
                        ),
                    ],
                ),
            )
        ],
        card_details=card_frame_bases.CardDetails(
            [
                {
                    "set_num": 0,
                    "card_num": 0,
                    "rarity": rarity.COMMON,
                    "image_url": "image_url",
                    "details_url": "details_url",
                    "is_in_draft_pack": "is_in_draft_pack",
                },
                {
                    "set_num": 0,
                    "card_num": 1,
                    "rarity": rarity.LEGENDARY,
                    "image_url": "image_url",
                    "details_url": "details_url",
                    "is_in_draft_pack": "is_in_draft_pack",
                },
            ]
        ),
    )
    assert len(sut) == 3
    # todo should probably assert entire output


def test_play_rate_frame_from_play_counts():
    sut = card_evaluation.PlayRateFrame.from_play_counts(
        play_count_frame=card_evaluation.PlayCountFrame(
            {
                "count_in_deck": [1, 2, 1],
                "decksearch_id": [0, 0, 0],
                "num_decks_with_count_or_less": [2, 1, 1],
                "card_num": [0, 0, 1],
                "details_url": ["details_url"] * 3,
                "image_url": ["image_url"] * 3,
                "is_in_draft_pack": [True] * 3,
                "rarity": [rarity.COMMON, rarity.COMMON, rarity.LEGENDARY,],
                "set_num": [0, 0, 0],
            }
        )
    )
    _ = sut.play_count
    assert len(sut) == 3


def test_play_value_frame_from_play_rates():
    sut = card_evaluation.PlayValueFrame.from_play_rates(
        play_rate_frame=card_evaluation.PlayRateFrame(
            {
                "count_in_deck": [1, 2, 1],
                "decksearch_id": [0, 0, 0],
                "num_decks_with_count_or_less": [2, 1, 1],
                "card_num": [0, 0, 1],
                "details_url": ["details_url"] * 3,
                "image_url": ["image_url"] * 3,
                "is_in_draft_pack": [True] * 3,
                "rarity": [rarity.COMMON, rarity.COMMON, rarity.LEGENDARY,],
                "set_num": [0, 0, 0],
                "play_rate": [16.25, 32.5, 16.25],
            }
        ),
        ownership=pd.DataFrame(
            {
                "set_num": {0: 0, 1: 0,},
                "card_num": {0: 0, 1: 1,},
                "count": {0: 1, 1: 0},
            }
        ),
    )

    _ = sut.play_value
    assert len(sut) == 3

    # todo should probably assert entire output


def test_play_craft_efficency_from_play_value():
    sut = card_evaluation.PlayCraftEfficiencyFrame.from_play_value(
        card_evaluation.PlayValueFrame(
            {
                "count_in_deck": [1, 2, 1],
                "decksearch_id": [0, 0, 0],
                "num_decks_with_count_or_less": [2, 1, 1],
                "card_num": [0, 0, 1],
                "details_url": ["details_url"] * 3,
                "image_url": ["image_url"] * 3,
                "is_in_draft_pack": [True] * 3,
                "rarity": [rarity.COMMON, rarity.COMMON, rarity.LEGENDARY,],
                "set_num": [0, 0, 0],
                "play_rate": [16.25, 32.5, 16.25],
                "play_value": [100, 50, 50],
                "is_owned": [True] * 3,
            }
        )
    )
    _ = sut.play_craft_efficiency
    assert len(sut) == 3


def test_own_value_frame_from_play_craft_efficency():
    sut = card_evaluation.OwnValueFrame.from_play_craft_efficiency(
        card_evaluation.PlayCraftEfficiencyFrame(
            {
                "count_in_deck": [1, 2, 1],
                "decksearch_id": [0, 0, 0],
                "num_decks_with_count_or_less": [2, 1, 1],
                "card_num": [0, 0, 1],
                "details_url": ["details_url"] * 3,
                "image_url": ["image_url"] * 3,
                "is_in_draft_pack": [True] * 3,
                "rarity": [rarity.COMMON, rarity.COMMON, rarity.LEGENDARY,],
                "set_num": [0, 0, 0],
                "play_rate": [16.25, 32.5, 16.25],
                "play_value": [100, 50, 50],
                "is_owned": [True] * 3,
                "craft_cost": [50, 50, 3200],
                "findability": [0.02623, 0.02623, 0],
                "play_craft_efficiency": [1.94755, 0.97377, 0.01562],
            }
        )
    )
    _ = sut.own_value
    assert len(sut) == 3
