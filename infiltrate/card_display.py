from dataclasses import dataclass

import numpy as np

from infiltrate import caches, models


# Todo clean up this mess


@caches.mem_cache.cache("card_displays", expire=3600)
def make_card_display(card_id: models.card.CardId) -> models.card.CardDisplay:
    # TODO depreciate
    """Makes a CardDisplay, utilizing the cache to avoid repeated work."""
    card_display = models.card.CardDisplay.from_card_id(card_id)
    return card_display


# def make_card_displays(card_ids: typing.List[models.card.CardId]) -> typing.List[models.card.CardDisplay]:
#     """Makes a batch of CardDisplays, to avoid multiple DB queries."""
#     cards = models.card.Card.query.all()  # todo ????
#
#     # card_display = models.card.CardDisplay.from_card_id(card_id)
#     return card_display


#     @dataclass
# class CardDisplay:
#     """Use make_card_display to use cached creation"""
#     set_num: int
#     card_num: int
#     name: str
#     rarity: models.rarity.Rarity
#     image_url: str
#     details_url: str
#
#     @classmethod
#     def from_card_id(cls, card_id: CardId):
#         """Makes a CardDisplay from a CardId.
#
#         This requires a db query and shouldn't be done many times."""
#         card = get_card(card_id.set_num, card_id.card_num)
#         return cls(set_num=card.set_num, card_num=card.card_num, name=card.name, rarity=card.rarity,
#                    image_url=card.image_url, details_url=card.details_url)
#
#     def to_dict(self):
#         return self.__dict__


@dataclass
class CardValueDisplay:
    """A bundle of values corresponding to a card, to be displayed in the front end."""
    card: models.card.CardDisplay
    count: int
    value: float

    @property
    def value_per_shiftstone(self):
        cost = models.rarity.rarity_from_name[self.card.rarity].enchant
        return self.value * 100 / cost

    def __str__(self):
        return f"{self.card.name}, {self.count}"

    def to_dict(self):
        self_dict = self.__dict__.copy()
        self_dict["value_per_shiftstone"] = self.value_per_shiftstone
        self_dict.pop('card')
        self_dict.update(self.card.to_dict())
        return self_dict

    @classmethod
    def from_card_id_with_value(cls, card_id_with_value: models.card.CardIdWithValue):
        """Creates a CardValueDisplay from a CardIdWithValue"""
        card = make_card_display(card_id_with_value.card_id)
        count = card_id_with_value.count
        value = card_id_with_value.value

        return cls(card, count, value)

    @classmethod
    def from_series(cls, series):
        card = models.card.CardDisplay(set_num=series.set_num, card_num=series.card_num,
                                       name=series.values[np.where(series.index == 'name')[0][0]],
                                       rarity=series.rarity, image_url=series.image_url,
                                       details_url=series.details_url)
        count = series.values[np.where(series.index == 'count')[0][0]]  # Gross. "count" is overwritten by a method.
        value = series.value
        return cls(card, count, value)

    # @classmethod
    # def from_card_id_with_value_bulk(cls, card_id_with_values: typing.List[models.card.CardIdWithValue]):
    #     cards = make_card_displays([c.card_id for c in card_id_with_values])
    #     counts = [c.count for c in card_id_with_values]
    #     values = [c.value for c in card_id_with_values]
