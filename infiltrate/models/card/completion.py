import typing as t

from fast_autocomplete import AutoComplete

import infiltrate.card_frame_bases as card_frame_bases
from infiltrate.models.card import Card_DF


def get_matching_card(card_df: Card_DF, search_str: str) -> Card_DF:
    """Return rows from the card_df with card names best matching
     the search."""
    matcher = _CardAutoCompleter(card_df)
    matches = matcher.get_cards_matching_search(search_str)
    return matches


class _CardAutoCompleter:
    def __init__(self, all_cards: card_frame_bases.CardDetails):
        self.cards = all_cards
        self.completer = self._init_autocompleter(self.cards)

    def get_cards_matching_search(self, search: str) -> Card_DF:
        """Returns cards with the name best matching the search string."""
        matches = self._match_name(search)
        name_pattern = "|".join(matches)
        cards_with_matching_name = self.cards[
            self.cards["name"].str.lower().str.fullmatch(name_pattern)
        ]

        return cards_with_matching_name

    def _match_name(self, search: str) -> t.List[str]:
        """Return the closest matching card name to the search string"""
        try:
            matches = self._search_without_normalizing(search, max_cost=3, size=3)
            match_strings = [match[0] for match in matches]
            return match_strings
        except IndexError:
            return []

    def _init_autocompleter(self, df: Card_DF):
        card_names = self._get_words(df)
        card_names_to_dicts = {word: {} for word in card_names}
        completer = AutoComplete(words=card_names_to_dicts)
        return completer

    @staticmethod
    def _get_words(df: Card_DF):
        names = df["name"]
        return names

    def _search_without_normalizing(self, word, max_cost=2, size=5):
        """
        parameters:
        - word: the word to return autocomplete results for
        - max_cost: Maximum Levenshtein edit distance to be considered
        - size: The max number of results to return
        """
        if not word:
            return []
        return list(self.completer._find_and_sort(word, max_cost, size))


class _AllCardAutoCompleter(_CardAutoCompleter):
    """Handles autocompleting searches to card names from ALL_CARDS"""

    # TODO make this update when the card database updates
    # TODO totally untested
    completer: AutoComplete = None

    def __init__(self, all_cards: card_frame_bases.CardDetails):
        if self.completer is None:
            super().__init__(all_cards)
