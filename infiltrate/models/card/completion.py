import typing as t

from fast_autocomplete import AutoComplete

import infiltrate.card_frame_bases as card_frame_bases
import infiltrate.card_evaluation as card_evaluation
from infiltrate.models.card import Card_DF


def get_matching_card(card_df: Card_DF, user, search_str: str) -> Card_DF:
    """Return rows from the card_df with card names best matching
     the search."""
    matcher = _CardAutoCompleter(card_df)
    match = matcher.get_cards_matching_search(user, search_str)
    return match


class _CardAutoCompleter:
    def __init__(self, all_cards: card_frame_bases.CardDetails):
        self.cards = all_cards
        self.completer = self._init_autocompleter(self.cards)

    def get_cards_matching_search(self, user, search: str) -> Card_DF:
        """Returns cards with the name best matching the search string."""
        name = self._match_name(search)
        cards = card_evaluation.OwnValueFrame(
            user, self.cards[self.cards["name"].str.lower() == name]
        )
        return cards

    def _match_name(self, search: str) -> t.Optional[str]:
        """Return the closest matching card name to the search string"""
        try:
            result = self.completer.search(word=search, max_cost=3, size=1)[0][0]
            return result
        except IndexError:
            return None

    def _init_autocompleter(self, df: Card_DF):
        words = self._get_words(df)
        words = {word: {} for word in words}
        completer = AutoComplete(words=words)
        return completer

    @staticmethod
    def _get_words(df: Card_DF):
        names = df["name"]
        return names


class _AllCardAutoCompleter(_CardAutoCompleter):
    """Handles autocompleting searches to card names from ALL_CARDS"""

    # TODO make this update when the card database updates
    # TODO totally untested
    completer: AutoComplete = None

    def __init__(self, all_cards: card_frame_bases.CardDetails):
        if self.completer is None:
            super().__init__(all_cards)
