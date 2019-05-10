from eternal_collection_guide.card import CardCollection
from eternal_collection_guide.values import ValueCollection


class Campaign:
    """A campaign in Eternal."""

    def __init__(self, name: str, set_num: int, card_collection: CardCollection, value_collection: ValueCollection):
        self.name = name
        self.set_num = set_num
        self.cards = card_collection
        self.value_collection = value_collection

    @property
    def average_value(self):
        cards_in_set = self.get_cards_in_set()

        total_value = 0
        for card in cards_in_set:
            value_set_of_missing_cards = self._get_values_of_card_by_name(card.name)
            value = sum(value_set_of_missing_cards)
            total_value += value

        return total_value

    def get_cards_in_set(self):
        cards_in_set = self.cards.get_cards_in_set(self.set_num)
        return cards_in_set

    def _get_values_of_card_by_name(self, card_name):
        value_sets = self.value_collection.dict["card_name"][card_name]
        if len(value_sets) == 0:
            return [0]
        return value_sets[0].values
