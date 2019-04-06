from base_learner import BaseLearner


class CardPlayset(object):
    def __init__(self, card_data, num_played):
        self.card_data = card_data
        self.num_played = num_played


class DeckData(object):
    def __init__(self, card_playsets, archetype, success=None):
        self.card_playsets = card_playsets
        self.archetype = archetype
        self.success = success
        pass

    @classmethod
    def from_deck_url(cls, url):
        pass  # fixme


class DeckLearner(BaseLearner):
    def __init__(self, file_prefix: str):
        super().__init__(file_prefix, "decks.json")

    def _update_contents(self):
        pass

    def _json_entry_to_content(self, json_entry):
        pass
