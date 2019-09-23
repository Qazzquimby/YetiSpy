"""Front end display of cards."""

# @caches.mem_cache.cache("card_displays", expire=3600)
# def make_card_display(card_id: models.card.CardId) -> models.card.CardDisplay:
#     # TODO depreciate
#     """Makes a CardDisplay, utilizing the cache to avoid repeated work."""
#     card_display = models.card.CardDisplay.from_card_id(card_id)
#     return card_display
#
#
# @dataclass
# class CardValueDisplay:
#     """A bundle of values corresponding to a card, to be displayed in the front end."""
#     card: models.card.CardDisplay
#     count: int
#     value: float
#
#     @property
#     def value_per_shiftstone(self): #TODO I'm moving this to functionality to card_displays. This class is redundant
#         """The card's value, per 100 shiftstone in it's crafting cost."""
#         cost = models.rarity.rarity_from_name[self.card.rarity].enchant
#         return self.value * 100 / cost
#
#     def __str__(self):
#         return f"{self.card.name}, {self.count}"
#
#     def to_dict(self):
#         """a dict representation of the object"""
#         self_dict = self.__dict__.copy()
#         self_dict["value_per_shiftstone"] = self.value_per_shiftstone
#         self_dict.pop('card')
#         self_dict.update(self.card.to_dict())
#         return self_dict
#
#     @classmethod
#     def from_card_id_with_value(cls, card_id_with_value: models.card.CardIdWithValue):
#         """Creates a CardValueDisplay from a CardIdWithValue"""
#         card = make_card_display(card_id_with_value.card_id)
#         count = card_id_with_value.count
#         value = card_id_with_value.value
#
#         return cls(card, count, value)
#
#     @classmethod
#     def from_series(cls, series):
#         """Creates a CardValueDisplay from a pandas series."""
#         card = models.card.CardDisplay(set_num=series.set_num, card_num=series.card_num,
#                                        name=series.values[np.where(series.index == 'name')[0][0]],
#                                        rarity=series.rarity, image_url=series.image_url,
#                                        details_url=series.details_url)
#         count = series.values[np.where(series.index == 'count')[0][0]]  # Gross. "count" is overwritten by a method.
#         value = series.value
#         return cls(card, count, value)
