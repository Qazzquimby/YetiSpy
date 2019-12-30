from unittest import TestCase

import pandas as pd

import models.deck_search
from evaluation import CardValueDataframeGetter


class TestCardValueDataframeGetter(TestCase):
    def test__merge_value_dfs(self):
        deck_search_value_dfs = [
            models.deck_search.DeckSearchValue_DF(
                {'set_num': [1, 1, 2],
                 'card_num': [1, 2, 1],
                 'count_in_deck': [1, 1, 1],
                 'decksearch_id': [1, 2, 3],
                 'value': [1, 3, 5]
                 }
            ),
            models.deck_search.DeckSearchValue_DF(
                {'set_num': [1, 1, 2],
                 'card_num': [1, 2, 2],
                 'count_in_deck': [1, 1, 1],
                 'decksearch_id': [1, 2, 3],
                 'value': [2, 4, 6]
                 }
            )
        ]
        sut = CardValueDataframeGetter

        summed_df = sut._merge_value_dfs(deck_search_value_dfs)
        self.assertTrue(summed_df['value'].equals(pd.Series([3, 7, 5, 6])))
